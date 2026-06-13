import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import os
import importlib.util
from sklearn.metrics import mean_squared_error, r2_score

# --- CONFIG ---
MODELS_DIR = 'tmp/air-quality-analysis-upstream/models/pipeline'
MAX_HORIZON = 72
BATCH_SIZE = 256
EPOCHS = 50
LEARNING_RATE = 1e-3
D_MODEL = 64
N_HEAD = 4
NUM_LAYERS = 2

# --- MODEL ---
class TimeSeriesTransformer(nn.Module):
    def __init__(self, enc_dim, dec_dim, d_model=64, nhead=4, num_layers=2):
        super(TimeSeriesTransformer, self).__init__()
        self.enc_proj = nn.Linear(enc_dim, d_model)
        self.dec_proj = nn.Linear(dec_dim, d_model)
        
        # 24 past + 72 future = 96 sequence steps
        self.pos_enc = nn.Parameter(torch.randn(1, 96, d_model))
        
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, batch_first=True)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        self.fc = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
        
    def forward(self, x_enc, x_dec, current_val):
        # x_enc: [B, 24, 14]
        # x_dec: [B, 72, 13]
        
        h_enc = self.enc_proj(x_enc)
        h_dec = self.dec_proj(x_dec)
        
        h_seq = torch.cat([h_enc, h_dec], dim=1) # [B, 96, d_model]
        h_seq = h_seq + self.pos_enc
        
        # Bidirectional attention across the whole sequence
        out_seq = self.transformer(h_seq)
        
        # We only care about predicting the 72 future steps
        future_out = out_seq[:, 24:, :] # [B, 72, d_model]
        
        deltas = self.fc(future_out).squeeze(-1) # [B, 72]
        pred_pm25 = current_val + torch.cumsum(deltas, dim=1)
        
        return pred_pm25

def weighted_mse_loss(input, target, weights):
    out = (input - target)**2
    out = out * weights
    return out.mean()

def train():
    # Load data from the LSTM script
    LSTM_SCRIPT = 'scripts/train_t72_accumulation_lstm.py'
    spec = importlib.util.spec_from_file_location("lstm_mod", LSTM_SCRIPT)
    lstm_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lstm_mod)
    
    (X_enc_train, X_dec_train, y_train, 
     X_enc_valid, X_dec_valid, y_valid, 
     c_train, c_valid) = lstm_mod.prep_data_lstm()
     
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    enc_dim = X_enc_train.shape[2]
    dec_dim = X_dec_train.shape[2]
    
    print(f"Training TimeSeriesTransformer on {device}")
    
    train_ds = TensorDataset(torch.FloatTensor(X_enc_train), torch.FloatTensor(X_dec_train), 
                             torch.FloatTensor(y_train), torch.FloatTensor(c_train))
    valid_ds = TensorDataset(torch.FloatTensor(X_enc_valid), torch.FloatTensor(X_dec_valid), 
                             torch.FloatTensor(y_valid), torch.FloatTensor(c_valid))
    
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    valid_loader = DataLoader(valid_ds, batch_size=BATCH_SIZE, shuffle=False)
    
    model = TimeSeriesTransformer(enc_dim, dec_dim, D_MODEL, N_HEAD, NUM_LAYERS).to(device)
    
    weights = torch.ones(MAX_HORIZON).to(device)
    weights[0] = 20.0
    weights[1] = 10.0
    weights[2] = 5.0
    
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    best_loss = float('inf')
    best_model_path = f'{MODELS_DIR}/t72_transformer_best.pt'
    
    for epoch in range(EPOCHS):
        model.train()
        t_loss = 0
        for b_enc, b_dec, by, bc in train_loader:
            b_enc, b_dec, by, bc = b_enc.to(device), b_dec.to(device), by.to(device), bc.to(device)
            optimizer.zero_grad()
            pred = model(b_enc, b_dec, bc)
            loss = weighted_mse_loss(pred, by, weights)
            loss.backward()
            optimizer.step()
            t_loss += loss.item()
            
        model.eval()
        v_loss = 0
        with torch.no_grad():
            for b_enc, b_dec, by, bc in valid_loader:
                b_enc, b_dec, by, bc = b_enc.to(device), b_dec.to(device), by.to(device), bc.to(device)
                pred = model(b_enc, b_dec, bc)
                v_loss += weighted_mse_loss(pred, by, weights).item()
        
        avg_v = v_loss / len(valid_loader)
        scheduler.step(avg_v)
        if (epoch+1) % 5 == 0 or epoch == 0:
            print(f"Epoch {epoch+1:02d}/{EPOCHS} | Train Loss: {t_loss/len(train_loader):.4f} | Valid Loss: {avg_v:.4f}")
        
        if avg_v < best_loss:
            best_loss = avg_v
            torch.save(model.state_dict(), best_model_path)
            
    # Evaluate Target T+24
    model.load_state_dict(torch.load(best_model_path, weights_only=True))
    model.eval()
    all_preds = []
    with torch.no_grad():
        for b_enc, b_dec, by, bc in valid_loader:
            b_enc, b_dec, bc = b_enc.to(device), b_dec.to(device), bc.to(device)
            pred = model(b_enc, b_dec, bc)
            all_preds.append(pred.cpu().numpy())
    
    y_pred = np.concatenate(all_preds)
    
    t24_idx = 23
    rmse_24 = np.sqrt(mean_squared_error(y_valid[:, t24_idx], y_pred[:, t24_idx]))
    
    print("\n--- Transformer Results ---")
    print(f"T+24h RMSE: {rmse_24:.3f}")
    
if __name__ == "__main__":
    if not os.path.exists(MODELS_DIR): os.makedirs(MODELS_DIR)
    train()
