# -*- coding: utf-8 -*-
"""HumanPresencePredictor.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1cM1G1PzXqJJlGhk1Bv7UXWFWYKJ4MRj5
"""

import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import keras
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense, Input
from keras.optimizers import Adam
from keras.losses import MeanSquaredError
from keras.metrics import MeanAbsoluteError
from sklearn.metrics import mean_squared_log_error
import numpy as np
import joblib


"""##This Project was made to predict from a series the presence of human in a room.
###This can enable us perform various automation tasks in a smart home
"""

# Commented out IPython magic to ensure Python compatibility.
# %pwd
# root path of my datas
# root_data_folder = ./cognit_data

# data description
# we have 50 rooms in an office building and in each room, we have collected data of:
# CO2 concentration, room air humidity, room temperature, luminosity, and PIR motion sensor data

# LETS CLEAR THE DIR INCASE WE HAD OLDFILES
# Base folder path
base_folder_path = "./cognit_data"

# List all directories (folders) inside the specified base folder path
folders = [f for f in os.listdir(base_folder_path) if os.path.isdir(os.path.join(base_folder_path, f))]

# Loop through each folder
for folder in folders:
    current_folder_path = os.path.join(base_folder_path, folder)
    files = os.listdir(current_folder_path)
    for file_name in files:
        if file_name.startswith("combined") and file_name.endswith(".csv"):
            file_path = os.path.join(current_folder_path, file_name)
            # Delete the file
            os.remove(file_path)
            print(f"Deleted file: {file_path}")

# Confirmation message
print("Deletion complete.")

# Extracting timestamp from one of the folders
# Base folder path
base_folder_path = "./cognit_data"

# List all directories (folders) inside the specified base folder path
folders = [f for f in os.listdir(base_folder_path) if os.path.isdir(os.path.join(base_folder_path, f))]
# print(folders[0])

sample_folder = folders[0]
sample_file = os.listdir(os.path.join(base_folder_path, sample_folder))[0]
sample_file_path = os.path.join(base_folder_path, sample_folder, sample_file)
sample_df = pd.read_csv(sample_file_path, usecols=[0], header=None)
timestamp = sample_df
# print(sample_df.head())
# print(sample_df.size)

# FIRST STEP LETS COMBINE THE DATA SO TAHT WE HAVE A GOOD SINGLE VIEW

# Base folder path
base_folder_path = "./cognit_data"

# List all directories (folders) inside the specified base folder path
folders = [f for f in os.listdir(base_folder_path) if os.path.isdir(os.path.join(base_folder_path, f))]

# Loop through each folder
for folder in folders:
    # Define the folder path for the current iteration
    current_folder_path = os.path.join(base_folder_path, folder)

    # Initialize an empty DataFrame to store the combined data
    combined_data = pd.DataFrame()

    # Initialize a list to store sensor data DataFrames, we concat late
    sensor_data_frames = []

    # Insert timestamp column into the empty DataFrame
    combined_data["Timestamp"] = timestamp

    # sensor number
    sensor_number = 1

    # Get a sorted list of file names in the current folder
    file_names = sorted(os.listdir(current_folder_path))

    # Loop through each file in the current folder
    for file_name in file_names:
        if file_name.endswith(".csv"):

            sensor_column_name = f"Sensor_{sensor_number}"

            # Read the CSV file into a DataFrame, selecting only the second column (sensor values)
            file_path = os.path.join(current_folder_path, file_name)
            room_data = pd.read_csv(file_path, usecols=[1], names=[sensor_column_name], header=None)  # Assuming second column contains sensor values

            # Append the DataFrame to the list
            sensor_data_frames.append(room_data)

            # Increment sensor number and generate column name for the next sensor
            sensor_number += 1


    # Concatenate the list of sensor data DataFrames along columns
    combined_data = pd.concat([combined_data] + sensor_data_frames, axis=1)

    # # Reset the index of the combined DataFrame
    # combined_data.reset_index(drop=True, inplace=True)

    # Save the combined DataFrame to a CSV file
    combined_file_path = os.path.join(current_folder_path, f"combined_data_{folder}.csv")
    combined_data.to_csv(combined_file_path, index=False)

    print("Combined data saved to:", combined_file_path)

# Confirmation message
print("All folders processed.")

# LETS DELETE ANY MATCHED ENTRY WE MAY ERRONEOUSLY HAVE
# Base folder path
base_folder_path = "./cognit_data"

# List all directories (folders) inside the specified base folder path
folders = [f for f in os.listdir(base_folder_path) if os.path.isdir(os.path.join(base_folder_path, f))]

# Loop through each folder
for folder in folders:
    current_folder_path = os.path.join(base_folder_path, folder)
    files = os.listdir(current_folder_path)
    for file_name in files:
        if file_name.startswith("combined_data_matched_") and file_name.endswith(".csv"):
            file_path = os.path.join(current_folder_path, file_name)
            # Delete the file
            os.remove(file_path)
            print(f"Deleted file: {file_path}")

# Confirmation message
print("Deletion complete.")

# NOW LETS CORRECT THE DIFFERENCE CAUSED IN THE SAMPLING TECHNIQUES 5s & 10s

# Base folder path
base_folder_path = "./cognit_data"

# List all directories (folders) inside the specified base folder path
folders = [f for f in os.listdir(base_folder_path) if os.path.isdir(os.path.join(base_folder_path, f))]

# Loop through each folder
for folder in folders:
    # Define the folder path for the current iteration
    current_folder_path = os.path.join(base_folder_path, folder)

    # Load the original dataset for the current room
    original_data_path = os.path.join(current_folder_path, f"combined_data_{folder}.csv")
    original_data = pd.read_csv(original_data_path)

    # Extract PIR sensor timestamps
    pir_timestamps = original_data.iloc[:, 4]  # Check PIR sensor is the 5th column (0-based index)

    # Resample other sensor measurements to match PIR sensor timestamps by picking every second sample
    others_resamp = original_data.iloc[::2, [0, 1, 2, 3, 5]]
    # The TECHNICALITY HERE -> THE ABOVE IS STORED IN ORDER
    # Combine resampled sensor measurements with PIR sensor measurements
    matched_data = pd.concat([others_resamp.iloc[:,0], others_resamp.iloc[:,1], others_resamp.iloc[:,2], others_resamp.iloc[:,3], pir_timestamps, others_resamp.iloc[:,4]], axis=1)

    # Drop rows with missing values
    matched_data_cleaned = matched_data.dropna()

    # Save the cleaned dataset to a CSV file
    matched_data_cleaned_path = os.path.join(current_folder_path, f"combined_data_matched_{folder}.csv")
    matched_data_cleaned.to_csv(matched_data_cleaned_path, index=False)

    # Print information about the matched dataset
    print(f"Matched and resampled dataset for {folder} saved to:", matched_data_cleaned_path)

# Confirmation message
print("All folders processed.")

# CLEAR TRUNCATIONS, IF ANY BEFORE

# Base folder path
base_folder_path = "./cognit_data"

# List all directories (folders) inside the specified base folder path
folders = [f for f in os.listdir(base_folder_path) if os.path.isdir(os.path.join(base_folder_path, f))]

# Loop through each folder
for folder in folders:
    current_folder_path = os.path.join(base_folder_path, folder)
    files = os.listdir(current_folder_path)
    for file_name in files:
        if file_name.startswith("combined_data_truncated_") and file_name.endswith(".csv"):
            file_path = os.path.join(current_folder_path, file_name)
            # Delete the file
            os.remove(file_path)
            print(f"Deleted file: {file_path}")

# Confirmation message
print("Deletion complete.")

# TRUNCATE THE DATA TO LENGTH OF TIMESTEPS COL
# Base folder path
base_folder_path = "./cognit_data"

# List all directories (folders) inside the specified base folder path
folders = [f for f in os.listdir(base_folder_path) if os.path.isdir(os.path.join(base_folder_path, f))]

# pick a sample file, to pick timestep
sample_folder = folders[0]
sample_file = os.listdir(os.path.join(base_folder_path, sample_folder))[0]
sample_file_path = os.path.join(base_folder_path, sample_folder, sample_file)
sample_df = pd.read_csv(sample_file_path, usecols=[0], header=None)
timestamp = sample_df

# Loop through each folder
for folder in folders:
    current_folder_path = os.path.join(base_folder_path, folder)
    combinedmatched_file_path = os.path.join(current_folder_path, f"combined_data_matched_{folder}.csv")

    combined_data = pd.read_csv(combinedmatched_file_path)

    timestamps = combined_data["Timestamp"]
    # Truncate all columns to match the length of the timestamps column
    for column in combined_data.columns:
        combined_data[column] = combined_data[column][:len(timestamp)]

    # Save the truncated DataFrame back to a CSV file
    truncated_file_path = os.path.join(current_folder_path, f"combined_data_truncated_{folder}.csv")
    combined_data.to_csv(truncated_file_path, index=False)

    print("Truncated data saved to:", truncated_file_path)

# Confirmation message
print("All folders processed.")

# A LITTLE INSIGHT TO SEE THAT THE DATA HAS SAME SIZE AS TIME STEP
base_folder_path = "./cognit_data"

# List all directories (folders) inside the specified base folder path
folders = [f for f in os.listdir(base_folder_path) if os.path.isdir(os.path.join(base_folder_path, f))]

for folder in folders:
  current_folder_path = os.path.join(base_folder_path, folder)
  files = os.listdir(current_folder_path)
  for file_name in files:
      if file_name.startswith("combined_data_truncated_") and file_name.endswith(".csv"):
          file_path = os.path.join(current_folder_path, file_name)
          viewfile = pd.read_csv(file_path)
          print(viewfile.info())

"""##NOW I HAVE DONE AND JOINED UP THE DATA FOR TEH SENSORS IN EACH ROOM
###OUR FOCUS => TO PREDICT FOR A PARTICULAR ROOM

###(FOR MISSING DATA WE WILL JUST DROP THE ENTIRE ROW)

#ROOM413
"""

# drop row of missing values, to keep data consistent
# Base folder path
base_folder_path = "./cognit_data"
room = '413'
room_path = os.path.join(base_folder_path,room,f"combined_data_truncated_{room}.csv")

# Load dataset for specific room
df = pd.read_csv(room_path)

# Drop rows with missing values or 'na'
df_clean = df.dropna()
print(df_clean.info())

"""####Let us generate the timesteps from the timestamp, remeber each entry counted by the Unix time, is now organized as seen here as a 10seconds pass. so we are starting from "2013-08-23 00:00:00" and adding on 10secs
#####we are going to generate this sequence and replace the timestep column, because we will later view this column as datetime object
"""

# generate time
start_time = pd.Timestamp("2013-08-23 00:00:00")

time_increment = pd.Timedelta(seconds=10)

# print(df.columns)
num_timestamps = len(df['Timestamp'])

# Generate the sequence of timestamps
timestamps = [start_time + i * time_increment for i in range(num_timestamps)]
timestamp_df = pd.DataFrame({'Timestamp': timestamps})
# print(timestamp_df.head())

# modified df
df['Timestamp'] = timestamp_df['Timestamp']
print(df.head())
# print(df.info())

# LETS ENGINEER-FEATURE OF DATES
# Feature engineering - Example: day of the week since date is in datetime format
df['date']=pd.to_datetime(df['Timestamp'])
df['year']=df['Timestamp'].dt.year
df['month']=df['Timestamp'].dt.month
df['day']=df['Timestamp'].dt.day
df['weekday']=df['Timestamp'].dt.dayofweek

df.drop(['Timestamp'],axis=1,inplace=True)

print(df.head())
print(df.info())

"""##EXPLORATORY DATA ANALYSIS

"""

print(df.info())
# actually the year is the same year, and the month is the same month if we calculate
# so i expect no correlation in these parts

# # Check correlation
# correlation_matrix = df.corr()

# plt.figure(figsize=(10, 8))
# sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f")
# plt.title('Correlation Matrix')
# plt.show()

# # okay so its the same year and month like we see

# drop year and month
df.drop(['year','month'], axis=1, inplace=True)

correlation_matrix = df.corr()
plt.figure(figsize=(10, 8))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f")
plt.title('Correlation Matrix')
plt.show()

sensors = ['Sensor_1', 'Sensor_2', 'Sensor_3', 'Sensor_4', 'Sensor_5']
colors = ['blue', 'orange', 'green', 'red', 'purple']

# Time series plot for Sensors
fig, axs = plt.subplots(nrows=len(sensors), ncols=1, figsize=(12, 8), sharex=True)

for i, sensor in enumerate(sensors):
    axs[i].plot(df['date'], df[sensor], label=sensor, color=colors[i])
    axs[i].set_title(f'Time Series Plot for {sensor}')
    axs[i].set_ylabel('Sensor Reading')
    axs[i].legend()

plt.xlabel('Date')
plt.tight_layout()
plt.show()

# how many are zeros here
# print(df['Sensor_4'].apply(lambda x: x == 0).sum()) #more than 97%

print(df.describe()) # most of the Sensor_4 is Zeros (Pir)


# # Lets see Histogram of sensor readings
# for i,sensor in enumerate(sensors):
#     plt.figure(figsize=(8, 6))
#     plt.hist(df[sensor], bins=20, density=True, color=colors[i], alpha=0.7)
#     sns.kdeplot(df[sensor], color='k', linestyle='--')
#     plt.title(f'Distribution of {sensor} Values')
#     plt.xlabel('Sensor Reading')
#     plt.ylabel('Density')
#     plt.show()

# Calculate threshold for PIR sensor, (LETS USE A THRESHOLD TO SAY IF SOMEONE IN ROOM)
pir_threshold = df['Sensor_4'].quantile(0.985)  # we need a threshold: Using 8th percentile as threshold
print(pir_threshold)
# Label occupancy based on threshold
df['occupancy'] = df['Sensor_4'].apply(lambda x: 1 if x > pir_threshold else 0)

# Print distribution of occupancy
print(df['occupancy'].value_counts())

# Plot occupancy distribution
plt.figure(figsize=(6, 4))
sns.countplot(data=df, x='occupancy', hue=df['occupancy'],palette=['skyblue', 'salmon'])
plt.title('Distribution of occupancy')
plt.xlabel('occupancy')
plt.ylabel('Count')
plt.show()

"""##WE WILL PREDICT THE FUTURE PIR VALUES AND THEN APPLY SIMILAR THRESHOLD TO DECIDE IF SOMEONE IS IN THE ROOM OR NOT

#####LETS PREPARE OUR DATA FOR USE IN LSTM TRAINING
"""

# UNCOMMENT AND DROP THESE IF YOU FACE CHALLENGES THEN COMMENT OUT AGAIN
# I HAD O DROP SENSOR 5 BECAUSE I DIDNF WANT TO INCLUDE IT WHEN PREDICTING FUTURE, ASSUMING THAT THE REST WERE CLOSELY TIED TO IT
# df.head()
# myY = df['Sensor_5']
# df.drop(['date', 'occupancy', 'Sensor_5'], axis=1, inplace=True)
# print(df.head())
# print(df.info())

# OUR X and y
X = df.values
y = myY.values
# print(X.shape)            #(36093,7)
# print(y.shape)            #(36093,1)

x_scaler=StandardScaler()
X=x_scaler.fit_transform(X)
X_train,X_valid,y_train,y_valid=train_test_split(X,y,test_size=0.2,random_state=42)
# print(X_train.shape)    #(28874, 7)
# print(X_valid.shape)    #(7219, 7)    #I have to drop one from this guy because sequence length used must match '2' in this case

# # slicing off the 3d dimension for valid
# X_valid = X_valid[:-1, :]
# # print(X_valid.shape)  # (7218, 7)

# Reshaping is essential for LSTM as it expects a 3 D input because it train in batches

# (number_of_batches, sequence_length, no_input_features)
X_train = X_train.reshape((28874, 1, X_train.shape[1]))  #basically 28874 batches
X_valid = X_valid.reshape((7219, 1, X_valid.shape[1]))

print('X_train_shape: ',X_train.shape) #=> result here (28874, 1, 7)  #the first is the 3d dimension actually
print('X_valid_shape: ',X_valid.shape) #=> result here (7219, 1, 7)

# ======================
y_scaler = MinMaxScaler()

y_train = y_scaler.fit_transform(y_train.reshape(-1,1))
y_valid = y_scaler.transform(y_valid.reshape(-1,1))

# # slicing off the 3d dimension for valid
# y_valid = y_valid[:-1, :]
# # print(y_valid.shape)  # (7218, 7)

# basically, (number_of_batches, sequence_length, no_outputfeatures)
y_train = y_train.reshape(28874, 1, 1)
y_valid = y_valid.reshape(7219, 1, 1)   #since i know i am expecting one prediction only as per sensor5
print('y_train_shape: ',y_train.shape)
print('y_valid_shape: ',y_valid.shape)

# SEQUENCE LENGTH MUST MATCH FOR TRAIN AND TEST DATA

# Save the scaler
joblib.dump(x_scaler, "./cognit_data/x_scaler.pkl")
joblib.dump(y_scaler, "./cognit_data/y_scaler.pkl")

"""###To save yourself extra calculations, you can use sequence length of 1, and you wouldnt have to calculate any extra stuff

this is what i later did

###BUILD OUR MODEL

IF YOU WILL RERUN ANYTHING BELOW THIS LINE MAKE SURE YOU RERUN THE CODE ABOVE IT FIRST BECAUSE THE VALUES MAY HAVE BEEN OVERWRITTEN RESCALLED BELOW
"""

### BUILD OUR LSTM MODEL
model=Sequential()
# basically, input shape => (sequence_length, no_outputfeatures)    #like x,y face of a matrix
model.add( LSTM(50,input_shape=(X_train.shape[1],X_train.shape[2])) )
model.add(Dense(1))
model.compile(loss='mean_squared_error',optimizer=Adam(learning_rate=0.001))
print(model.summary())


# I AM PREDICTING A SINGLE OUTPUT OF THE SINGLE PIR(Sensor_5) VARIABLE...

## TRAIN
history = model.fit(X_train,y_train,epochs=9,batch_size=512,validation_data=(X_valid,y_valid),verbose=1)

# Save the trained model
model.save("./cognit_data/mymodel.h5")
# Save the weights
model.save_weights("./cognit_data/mymodel_weights.h5")
# Save the history for compare
joblib.dump(history.history, './cognit_data/lstm_history.joblib')

# VALID PREDS
preds=model.predict(X_valid)

"""#####Basically for each batch of (1,7) we indeed have up to 50 outputs but the Dense layer uses these to make a prediction of just one value which corresponds to the single output variable of our choice.

#####Finally, the next prediction corresponds to the next timestep and in this case, when it is processed the next (1,7) in same batch including some knowlege from the previous timestep, then basically we get another predition for a time step that should naturally come after the last time step.

this is contined and eventually we get to the last batch which contains the last set of time steps,
So the last batch will be the lastset of timesteps.

###Summary: the batches contain different timesteps that naturally follow each other.
"""

#WE ONLY INCREASE THE DENSE LAYER WHEN WE WANT MORE THAN ONE OUTPUT SET IN THE OUTPUT
#BASICALLY IF THE DESE MAKES TWO PREDICTIONS EACH TIME AFTER PROCESSING A BATCH THIS
#MEANS THAT [Y1, Y2] ARE THE CUURENT VALUES FOR THAT PROCESSED TIMESTEP
#SO WHEN WE FINISH WITH (batchsize, [denselayersize]) each batchsize entry is thus a
#pair occuring at the timestamp

# ============================================
model2 = keras.models.load_model("./cognit_data/mymodel.h5")
preds2 = model2.predict(X_valid)
print(model2.summary())
# ============================================
# Load the scalers
x_scaler = joblib.load("./cognit_data/x_scaler.pkl")
y_scaler = joblib.load("./cognit_data/y_scaler.pkl")
# ============================================
# JUST TEST
# INVERTING
preds_actual = y_scaler.inverse_transform(preds2)
y_valid_actual = y_scaler.inverse_transform(y_valid.reshape(-1,1))



# ============================================
preds_flat = preds_actual.flatten()
y_valid_flat = y_valid_actual.flatten()

# Evaluate the LSTM model using RMSLE
rmsle = np.sqrt(mean_squared_log_error(y_valid_flat,preds_flat))
print("LSTM RMSLE:", rmsle)

plt.scatter(y_valid_flat, preds_flat, color='yellow', label='Predicted')
plt.xlabel('Actual values')
plt.ylabel('Predicted values')
plt.title('Model performance LSTM')
plt.legend()
plt.show()

# more visaulizations of how performed

plt.figure(figsize=(10, 6))
# Plot actual values for the first few samples
plt.plot(y_valid_flat[:100], label='Actual', color='blue')

# Plot predicted values for the first few samples
plt.plot(preds_flat[:100], label='Predicted', color='orange')

plt.title('Actual vs. Predicted Values (First 100 Samples)')
plt.xlabel('Sample Index')
plt.ylabel('Sensor_5 Value')
plt.legend()
plt.show()

"""#NEXT PHASE, LETS LOOK AT THE PREDICTION AND MAKE SOME CHOICE OF THRESHOLD FOR PERSON IN A ROOM"""

mydf = pd.DataFrame({'occupancy_pred': preds_flat, 'actual': y_valid_flat})

print(mydf.info())
print(mydf.describe())

sns.histplot(data=mydf, x='occupancy_pred', kde=True)
plt.title('Distribution of occupancy_pred')
plt.xlabel('Predictions')
plt.ylabel('Frequency')
plt.show()

sns.histplot(data=mydf, x='actual', kde=True)
plt.title('Distribution of actual_occupancy')
plt.xlabel('actual_values')
plt.ylabel('Frequency')
plt.show()

threshold = 24.5

mydf['pred_label'] = mydf['occupancy_pred'].apply(lambda x: 1 if x > threshold else 0)
mydf['actual_label'] = mydf['actual'].apply(lambda x: 1 if x > threshold else 0)

mydf['mismatch'] = mydf.apply(lambda x: 1 if (x['pred_label'] != x['actual_label']) else 0, axis=1)
print(mydf.head())

mydf.to_csv('./cognit_data/predslabels.csv', index=False)
