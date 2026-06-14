import pandas as pd
import numpy as np
import os
import glob

RAW_DATA_DIR = "/home/uno/working/bioinfo/airdb/csv_output"
OUTPUT_DIR = "../../data/processed/pm25_collocation"

def load_and_clean_sensor(file_name, time_col='time', pm_col='pm2_5_cf', extra_cols=None):
    filepath = os.path.join(RAW_DATA_DIR, file_name)
    if not os.path.exists(filepath):
        print(f"Warning: {file_name} not found.")
        return pd.DataFrame()
        
    usecols = [time_col, pm_col]
    if extra_cols:
        usecols.extend(extra_cols)
        
    df = pd.read_csv(filepath, usecols=usecols)
    df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
    df = df.dropna(subset=[time_col])
    df.set_index(time_col, inplace=True)
    
    # 1. Range Checks (QA/QC)
    df[pm_col] = pd.to_numeric(df[pm_col], errors='coerce')
    df.loc[(df[pm_col] < 0) | (df[pm_col] > 2000), pm_col] = np.nan
    
    # 2. Resample to 1-hour intervals
    # We require at least 15 minutes of valid data per hour (25% completeness) 
    # to keep it simple for now. 
    df_hourly = df.resample('1h').mean()
    
    return df_hourly

def main():
    print("Ingesting and cleaning PM2.5 Data...")
    
    # Load Core Unit (PMS7003)
    mlab_p1 = load_and_clean_sensor('mlab_p1.csv', time_col='time', pm_col='pm2_5_cf')
    mlab_p1.rename(columns={'pm2_5_cf': 'mlab_pms7003_pm25'}, inplace=True)
    
    # Load Dylos (Mid-Tier Anchor)
    dylos = load_and_clean_sensor('dylos.csv', time_col='time', pm_col='pm2_5_f')
    dylos.rename(columns={'pm2_5_f': 'dylos_pm25_fit'}, inplace=True)
    
    # Load AirVisual (Consumer Anchor & Environmental Context)
    airvisual = load_and_clean_sensor('airvisual.csv', time_col='time', pm_col='pm25', extra_cols=['temp', 'humid'])
    airvisual.rename(columns={'pm25': 'airvisual_pm25', 'temp': 'env_temp', 'humid': 'env_humid'}, inplace=True)
    
    # Merge datasets
    merged = mlab_p1.join(dylos, how='outer').join(airvisual, how='outer')
    
    # Filter for valid dates based on our campaign plan (Jan 2019 to Aug 2022)
    merged = merged['2019-01-01':'2022-08-31']
    
    # Drop rows where all PM2.5 data is missing
    merged.dropna(how='all', subset=['mlab_pms7003_pm25', 'dylos_pm25_fit', 'airvisual_pm25'], inplace=True)
    
    # Create Output directory if not exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, 'hourly_collocation_merged.csv')
    merged.to_csv(output_path)
    print(f"Data cleaned and saved to {output_path}")
    print(merged.describe())

if __name__ == "__main__":
    main()
