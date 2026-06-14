import torch
import numpy as np
from sklearn.metrics import mean_squared_error
from scripts.train_t72_transformer import TimeSeriesTransformer, MODELS_DIR
import importlib.util

LSTM_SCRIPT = 'scripts/train_t72_accumulation_lstm.py'
spec = importlib.util.spec_from_file_location("lstm_mod", LSTM_SCRIPT)
lstm_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lstm_mod)

(_, _, _, X_enc_valid, X_dec_valid, y_valid, _, c_valid) = lstm_mod.prep_data_lstm()

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
enc_dim = X_enc_valid.shape[2]
dec_dim = X_dec_valid.shape[2]

model = TimeSeriesTransformer(enc_dim, dec_dim, d_model=64, nhead=4, num_layers=2).to(device)
best_model_path = f'{MODELS_DIR}/t72_transformer_best.pt'
model.load_state_dict(torch.load(best_model_path, weights_only=True))
model.eval()

from torch.utils.data import TensorDataset, DataLoader
valid_ds = TensorDataset(torch.FloatTensor(X_enc_valid), torch.FloatTensor(X_dec_valid), 
                         torch.FloatTensor(y_valid), torch.FloatTensor(c_valid))
valid_loader = DataLoader(valid_ds, batch_size=256, shuffle=False)

all_preds = []
with torch.no_grad():
    for b_enc, b_dec, by, bc in valid_loader:
        b_enc, b_dec, bc = b_enc.to(device), b_dec.to(device), bc.to(device)
        pred = model(b_enc, b_dec, bc)
        all_preds.append(pred.cpu().numpy())

y_pred = np.concatenate(all_preds)

for h in [48, 72]:
    rmse = np.sqrt(mean_squared_error(y_valid[:, h-1], y_pred[:, h-1]))
    print(f"Transformer T+{h}h RMSE: {rmse:.3f}")

