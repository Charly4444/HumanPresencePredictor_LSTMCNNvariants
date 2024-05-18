# -*- coding: utf-8 -*-
"""CNNbasedHumanPresencePredictor.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1L2dpSlV5z4BZ_ALMQqCgI3Cz4o2fyKWC
"""

import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import keras
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from keras.models import Sequential
from keras.layers import Conv1D, MaxPooling1D, Flatten, Dense
from keras.optimizers import Adam
from keras.losses import MeanSquaredError
from keras.metrics import MeanAbsoluteError
from sklearn.metrics import mean_squared_log_error
import numpy as np
import joblib


"""##This Project was made to predict from a series the presence of human in a room. We make this modification with CNN"""

# Commented out IPython magic to ensure Python compatibility.
# %pwd

# data description
# we have 50 rooms in an office building and in each room, we have collected data of:
# CO2 concentration, room air humidity, room temperature, luminosity, and PIR motion sensor data

# Extracting timestamp from one of the folders
# Base folder path
base_folder_path = "./cognit_data"

"""#ROOM413"""

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

"""####Let us make timesteps as 10seconds pass. so we are starting from "2013-08-23 00:00:00" and adding on 10secs.. Like we did before but now CNN"""

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
# I HAD TO DROP SENSOR 5 BECAUSE I DIDNF WANT TO INCLUDE IT WHEN PREDICTING FUTURE, ASSUMING THAT THE REST WERE CLOSELY TIED TO IT
df.head()
myY = df['Sensor_5']
df.drop(['date', 'occupancy', 'Sensor_5'], axis=1, inplace=True)
print(df.head())
print(df.info())

# OUR X and y
X = df.values
y = myY.values
# print(X.shape)            #(36093,6)
# print(y.shape)            #(36093,1)

x_scaler=StandardScaler()
X=x_scaler.fit_transform(X)
X_train,X_valid,y_train,y_valid=train_test_split(X,y,test_size=0.2,random_state=42)
# print(X_train.shape)    #(28874, 6)
# print(X_valid.shape)    #(7219, 6)


# Reshaping is essential aslike previous model CNN will need 3D input to train in batches

# (number_of_batches, sequence_length, no_input_features)
X_train = X_train.reshape((X_train.shape[0], 1, X_train.shape[1]))  #basically 28874 batches
X_valid = X_valid.reshape((X_valid.shape[0], 1, X_valid.shape[1]))

print('X_train_shape: ',X_train.shape) #=> result here (28874, 1, 6)  #the first is the 3d dimension actually
print('X_valid_shape: ',X_valid.shape) #=> result here (7219, 1, 6)

# ======================
y_scaler = MinMaxScaler()

y_train = y_scaler.fit_transform(y_train.reshape(-1,1))
y_valid = y_scaler.transform(y_valid.reshape(-1,1))

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

###OUR CNN MODEL HERE

OUR DATA IS READY AND IN 3D MODE THEN WE NOW GET TO OUR CNN MODEL
"""

### BUILD CNN MODEL
model=Sequential()
# basically, input shape => (sequence_length, no_outputfeatures)    #like x,y face of 3d matrix
# Create the CNN model
model_cnn = Sequential()

# Add a 1D convolutional layer
model_cnn.add(Conv1D(filters=64, kernel_size=8, activation='relu', input_shape=(X_train.shape[1], X_train.shape[2]), padding='same'))

# Add a max pooling layer
model_cnn.add(MaxPooling1D(pool_size=2, padding='same'))

# Flatten the output from the convolutional layer
model_cnn.add(Flatten())

# Add a dense layer
model_cnn.add(Dense(50, activation='relu'))

# Add the output layer
model_cnn.add(Dense(1, activation='linear'))

# Compile the model
model_cnn.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])

# Print the model summary
print(model_cnn.summary())

# ==
# I AM PREDICTING A SINGLE OUTPUT OF THE PIR(Sensor_5) VARIABLE... like before

## TRAIN
history = model_cnn.fit(X_train,y_train,epochs=12,batch_size=512,validation_data=(X_valid,y_valid),verbose=1)

# Save the trained model
model_cnn.save("./cognit_data/mycnnmodel.h5")
# Save the weights
model_cnn.save_weights("./cognit_data/mycnnmodel_weights.h5")
# Save the history for compare
joblib.dump(history.history, './cognit_data/cnn_history.joblib')
# VALID PREDS
preds=model.predict(X_valid)

"""####Now our CNN will work normally and for now we fixed a prediction size for it at 300.
#####We will adjust as we go on from here.
"""

#WE ONLY INCREASE THE DENSE LAYER WHEN WE WANT MORE THAN ONE OUTPUT SET IN THE OUTPUT
#BASICALLY IF THE DESE MAKES TWO PREDICTIONS EACH TIME AFTER PROCESSING A BATCH THIS
#MEANS THAT [Y1, Y2] ARE THE CUURENT VALUES FOR THAT PROCESSED TIMESTEP
#SO WHEN WE FINISH WITH (batchsize, [denselayersize]) each batchsize entry is thus a
#basically output always showing up as [batchsize, novarsOutput]

# ============================================
model2 = keras.models.load_model("./cognit_data/mycnnmodel.h5")
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

mydf.to_csv('./cognit_data/CNNpredslabels.csv', index=False)