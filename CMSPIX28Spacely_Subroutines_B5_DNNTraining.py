# spacely
try:
    from Master_Config import *
except:
    print("Cannot import Master_Config likely you are not running spacely.")

# os settings
import os
os.environ['TF_XLA_FLAGS'] = '--tf_xla_enable_xla_devices'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Standard library imports
import math
import h5py
from fxpmath import Fxp
import pandas as pd
import csv

# Third-party imports
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import tensorflow as tf
from pandas import read_csv
from sklearn.metrics import classification_report, confusion_matrix, mean_squared_error
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import StandardScaler
import hls4ml

# TensorFlow imports
from tensorflow.keras import datasets, layers, models
from tensorflow.keras.callbacks import CSVLogger, EarlyStopping
from tensorflow.keras.layers import Activation, Conv2D, Dense, Dropout, Flatten, Input, Lambda, MaxPooling2D
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import SparseCategoricalCrossentropy
from tensorflow.keras.metrics import SparseCategoricalAccuracy
from tensorflow.keras.utils import Progbar
from tensorflow.keras.models import clone_model

# QKeras imports
from qkeras import *

# number with dense
def CreateModel(shape, nb_classes, first_dense):
    x = x_in = Input(shape, name="input")
    x = Dense(first_dense, name="dense1")(x)
    x = keras.layers.BatchNormalization()(x)
    x = Activation("relu", name="relu1")(x)
    x = Dense(nb_classes, name="dense2")(x)
    x = Activation("linear", name="linear")(x)
    model = Model(inputs=x_in, outputs=x)
    return model

# Fold BatchNormalization in QDense
def CreateQModel(shape, nb_classes):
    x = x_in = Input(shape, name="input1")
    x = QDenseBatchnorm(58,
      kernel_quantizer=quantized_bits(4,0,alpha=1),
      bias_quantizer=quantized_bits(4,0,alpha=1),
      name="dense1")(x)
    x = QActivation("quantized_relu(8,0)", name="relu1")(x)
    x = QDense(3,
        kernel_quantizer=quantized_bits(4,0,alpha=1),
        bias_quantizer=quantized_bits(4,0,alpha=1),
        name="dense2")(x)
    x = Activation("linear", name="linear")(x)
    model = Model(inputs=x_in, outputs=x)
    return model

# convert code from hsl4ml style output to chip style input
def prepareWeights(path):
    data_fxp = Fxp(None, signed=True, n_word=4, n_int=0)
    data_fxp.rounding = 'around'
    def to_fxp(val):
        return data_fxp(val)

    b5_data = pd.read_csv(os.path.join(path, 'b5.txt'), header=None)
    w5_data = pd.read_csv(os.path.join(path, 'w5.txt'), header=None)
    b2_data = pd.read_csv(os.path.join(path, 'b2.txt'), header=None)
    w2_data = pd.read_csv(os.path.join(path, 'w2.txt'), header=None)
    # print(b5_data)

    b5_data_list = []
    w5_data_list = []
    b2_data_list = []
    w2_data_list = []

    for i in range(2, -1, -1):
        b5_data_list.append(to_fxp(b5_data.values[0][i]).bin())

    for i in range(173, -1, -1):
        w5_data_list.append(to_fxp(w5_data.values[0][i]).bin())

    for i in range(57, -1, -1):
        b2_data_list.append(to_fxp(b2_data.values[0][i]).bin())

    for i in range(927, -1, -1):
        w2_data_list.append(to_fxp(w2_data.values[0][i]).bin())

    b5_bin_list = [int(bin_string) for data in b5_data_list for bin_string in data]
    w5_bin_list = [int(bin_string) for data in w5_data_list for bin_string in data]
    b2_bin_list = [int(bin_string) for data in b2_data_list for bin_string in data]
    w2_bin_list = [int(bin_string) for data in w2_data_list for bin_string in data]
    pixel_list = [0 for _ in range(512)]
    b5_w5_b2_w2_pixel_list = b5_bin_list + w5_bin_list + b2_bin_list + w2_bin_list + pixel_list

    csv_file = os.path.join(path, 'b5_w5_b2_w2_pixel_bin.csv')
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(b5_w5_b2_w2_pixel_list)
    
    return csv_file

def input_to_pixelout(x):
    N_INFERENCES = x.shape[0]

    # first create compout
    encoder_values_Ninferences = []
    for i in range(N_INFERENCES):
        encoder_values = []
        for j in range(16):
            a = x[i][j]
            encoder_sum = []
            if(a==0):
                encoder_sum = [0 for _ in range(16)]
                encoder_sum.reverse()
                
            elif(a==1):
                encoder_sum = [1]+[0 for _ in range(15)]
                encoder_sum.reverse()

            elif(a==2):
                encoder_sum = [2]+[0 for _ in range(15)]
                encoder_sum.reverse()

            elif(a==3):
                encoder_sum = [3]+[0 for _ in range(15)]
                encoder_sum.reverse()

            else:
                l3=[]
                if a%3 == 0:
                    result = int(a/3)
                    l3 = [3 for _ in range(result)]
                    l_diff = 16-len(l3)
                    encoder_sum = l3 + [0 for _ in range(l_diff)]
                    encoder_sum.reverse()
                else:
                    result = int(a//3)
                    l3 = [3 for _ in range(result)]
                    diff = a-sum(l3)
                    l3.append(diff)
                    l_diff = 16-len(l3)
                    encoder_sum = l3 + [0 for _ in range(l_diff)]
                    encoder_sum.reverse()

            encoder_values.append(encoder_sum)
        encoder_values = [j for i in encoder_values for j in i]
        encoder_values_Ninferences.append(encoder_values)
        
    compout_values_Ninferences = []
    for i in range(N_INFERENCES):
        compout_values = []
        for j in range(256):
            a = encoder_values_Ninferences[i][j]
            if(a==3):
                compout_values.append(7)
            elif(a==2):
                compout_values.append(3)
            elif(a==1):
                compout_values.append(1)
            else:
                compout_values.append(0)
        compout_values_Ninferences.append(compout_values)

    return compout_values_Ninferences

class ModelPipeline:
    def __init__(self, model, optimizer, train_acc_metric, val_acc_metric, batch_size=32, asic_training=False):
        self.model = model
        self.optimizer = optimizer
        self.train_acc_metric = train_acc_metric
        self.val_acc_metric = val_acc_metric
        self.batch_size = batch_size
        self.asic_training = asic_training
        
        # Initialize custom loss function
        self.loss_fn = self.custom_loss_function

    def print_model(self):
        """
        Iterate through each layer and print weights and biases
        """
        for layer in self.model.layers:
            print(f"Layer: {layer.name}")
            for weight in layer.weights:
                print(f"  {weight.name}: shape={weight.shape}")
                print(f"    Values:\n{weight.numpy()}\n")

    def custom_loss_function(self, y_true, y_pred):
        """
        Custom loss function.
        Default: Sparse Categorical Crossentropy with from_logits=True.
        Modify this function as needed.
        """
        loss = tf.keras.losses.sparse_categorical_crossentropy(y_true, y_pred, from_logits=True)
        return tf.reduce_mean(loss)

    def split_data(self, x_data, y_data, test_size=0.2, shuffle=True, random_state=42):
        """
        Splits data into training and testing datasets.
        """
        x_train, x_val, y_train, y_val = train_test_split(
            x_data, y_data, test_size=test_size, random_state=random_state, shuffle=shuffle
        )
        self.train_dataset = tf.data.Dataset.from_tensor_slices((x_train, y_train)).batch(self.batch_size)
        self.val_dataset = tf.data.Dataset.from_tensor_slices((x_val, y_val)).batch(self.batch_size)
    
    # @tf.function
    def forward_pass(self, x, training=False):
        """
        Performs a forward pass of the model.
        """
        return self.model(x, training=training)
    
    def prepare_weights_asic(self, x):        

        # write the current weights to file
        config = hls4ml.utils.config_from_keras_model(self.model, granularity='name')
        # Convert to an hls model
        hls_model = hls4ml.converters.convert_from_keras_model(self.model, hls_config=config, output_dir='./tmp/test_prj')
        hls_model.write()
        dnn_csv = prepareWeights("./tmp/test_prj/firmware/weights/")
        
        # generate input csv
        pixelout = input_to_pixelout(x) #.numpy())
        pixel_compout_csv = './tmp/compouts.csv'
        with open(pixel_compout_csv, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(pixelout)

        return dnn_csv, pixel_compout_csv

    def forward_pass_asic(self, x, dnn_csv = None, pixel_compout_csv = None):
        """
        Performs a forward pass of the model on the asic
        """

        print("   within forward pass asic")

        # run to chip -> output saved to readout.csv
        freq = '28'
        DNN(
            progDebug=False, loopbackBit=0, patternIndexes = range(3), verbose=False, # update range when finished
            vinTest='1D', freq=freq, startBxclkState='0',scanloadDly='13', 
            progDly='5', progSample='20', progResetMask='0', progFreq='64', 
            testDelaySC='08', sampleDelaySC='08', bxclkDelay='0B', configClkGate='0',  
            dnn_csv = dnn_csv,
            pixel_compout_csv = pixel_compout_csv,
            outDir = "./tmp",
        )
        #Take in the pixel_compout_csv files and return the DNN output value in decimal
        dnnOut=DNN_analyse(debug=False, latency_bit=20,  bxclkFreq=freq, readout_CSV = "./tmp/readout.csv" )
        print(dnnOut.shape)
        return dnnOut


    # @tf.function
    def train_step(self, 
                   x_batch, y_batch, 
                   dnn_csv = None, pixel_compout_csv = None # for asic training
    ):
        """
        Performs a single training step.
        """

        with tf.GradientTape() as tape:
            # evaluate model off
            print("Forward pass")
            logits = self.forward_pass(x_batch, training=True)
            loss_value = self.loss_fn(y_batch, logits)
            # evaluate model on chip
            if self.asic_training:
                print("Forward pass asic")
                logits_asic = self.forward_pass_asic(x_batch, dnn_csv, pixel_compout_csv)
                # loss_value_asic = self.loss_fn(y_batch, logits_asic)
                # sum them
                # loss_value = loss_value + loss_value_asic

        grads = tape.gradient(loss_value, self.model.trainable_weights)
        self.optimizer.apply_gradients(zip(grads, self.model.trainable_weights))
        self.train_acc_metric.update_state(y_batch, logits)
        return loss_value

    # @tf.function
    def val_step(self, x_batch, y_batch):
        """
        Performs a single validation step.
        """
        logits = self.forward_pass(x_batch, training=False)
        val_loss = self.loss_fn(y_batch, logits)
        self.val_acc_metric.update_state(y_batch, logits)
        return val_loss

    def train(self, epochs, patience=20):
        """
        Trains the model for a specified number of epochs with early stopping.
        """
        best_val_loss = float("inf")
        wait = 0
        best_weights = None

        for epoch in range(epochs):
            print(f"Epoch {epoch + 1}/{epochs}")

            # Training loop
            train_loss = 0
            train_steps = len(self.train_dataset)
            train_progbar = Progbar(target=train_steps, stateful_metrics=["loss", "sparse_categorical_accuracy"])
            
            for step, (x_batch, y_batch) in enumerate(self.train_dataset):
                print(f"Batch {step}/{len(self.train_dataset)}")

                # prepare weights for asic
                if self.asic_training:
                    dnn_csv, pixel_compout_csv = self.prepare_weights_asic(x_batch)
                    loss_value = self.train_step(x_batch, y_batch, dnn_csv, pixel_compout_csv)
                else:
                    loss_value = self.train_step(x_batch, y_batch)
                
                # do training step
                # loss_value = self.train_step(x_batch, y_batch, dnn_csv, pixel_compout_csv)
                train_loss += loss_value
                train_acc = self.train_acc_metric.result()
                train_progbar.update(step + 1, values=[("loss", loss_value.numpy()), ("sparse_categorical_accuracy", train_acc.numpy())])

            train_loss /= train_steps
            train_acc = self.train_acc_metric.result()
            self.train_acc_metric.reset_states()

            # Validation loop
            val_loss = 0
            val_steps = len(self.val_dataset)
            val_progbar = Progbar(target=val_steps, stateful_metrics=["val_loss", "val_sparse_categorical_accuracy"])
            
            for step, (x_batch, y_batch) in enumerate(self.val_dataset):
                val_loss_batch = self.val_step(x_batch, y_batch)
                val_loss += val_loss_batch
                val_acc = self.val_acc_metric.result()
                val_progbar.update(step + 1, values=[("val_loss", val_loss_batch.numpy()), ("val_sparse_categorical_accuracy", val_acc.numpy())])

            val_loss /= val_steps
            val_acc = self.val_acc_metric.result()
            self.val_acc_metric.reset_states()

            # Early stopping logic
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                wait = 0
                best_weights = self.model.get_weights()
            else:
                wait += 1
                if wait >= patience:
                    print("Early stopping triggered.")
                    self.model.set_weights(best_weights)
                    break
        
def DNNTraining(asic_training=False):
    
    # create model
    shape = 16 # y-profile ... why is this 16 and not 8?
    nb_classes = 3 # positive low pt, negative low pt, high pt
    first_dense = 58 # shape of first dense layer

    mtype = "qkeras"

    # keras
    if mtype == "keras":
        # initiate model
        model = CreateModel(shape, nb_classes, first_dense)
        model.summary()
        # load the model
        model_file = "/fasic_home/gdg/research/projects/CMS_PIX_28/directional-pixel-detectors/multiclassifier/models/ds8l6_padded_noscaling_keras_d58model.h5"
        model = tf.keras.models.load_model(model_file)

    # qkeras
    if mtype == "qkeras":
        # initiate model
        model = CreateQModel(shape, nb_classes)
        model.summary()
        # load the model
        model_file = "/fasic_home/gdg/research/projects/CMS_PIX_28/directional-pixel-detectors/multiclassifier/models/ds8l6_padded_noscaling_qkeras_foldbatchnorm_d58w4a8model.h5"
        co = {}
        utils._add_supported_quantized_objects(co)
        model = tf.keras.models.load_model(model_file, custom_objects=co)
        # Generate a simple configuration from keras model
        config = hls4ml.utils.config_from_keras_model(model, granularity='name')
        # Convert to an hls model
        hls_model = hls4ml.converters.convert_from_keras_model(model, hls_config=config, output_dir='test_prj')
        hls_model.write()
        # prepare weights
        prepareWeights("test_prj/firmware/weights/")

    # load example inputs and outputs
    x_test = pd.read_csv("/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_D/tb/dnn/csv/l6/input_1.csv", header=None)
    x_test = np.array(x_test.values.tolist())
    y_test = pd.read_csv("/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_D/tb/dnn/csv/l6/layer7_out_ref_int.csv", header=None)
    y_test = np.array(y_test.values.tolist()).flatten()
    print(x_test.shape, y_test.shape)
    
    # decide if train
    train_and_save = True # <<< PAY ATTENTION <<<
    model_file = 'model.h5' if train_and_save == True else model_file # use default value
    history = None
    if train_and_save:
        
        optimizer = tf.keras.optimizers.Adam()
        # loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
        train_acc_metric = tf.keras.metrics.SparseCategoricalAccuracy()
        val_acc_metric = tf.keras.metrics.SparseCategoricalAccuracy()

        # Initialize pipeline
        pipeline = ModelPipeline(model, optimizer, train_acc_metric, val_acc_metric, batch_size=1024, asic_training=asic_training)
        pipeline.split_data(x_test, y_test)
        pipeline.train(epochs=10, patience=5)

        # save model
        model.save(model_file)
        print('Save:', model_file)

        # load model
        co = {}
        utils._add_supported_quantized_objects(co)
        model = tf.keras.models.load_model(model_file, custom_objects=co)

    # get loss, accuracy
    loss, accuracy = model.evaluate(x_test, y_test)
    print(f"Test loss: {loss}")
    print(f"Test accuracy: {accuracy}")

    # # make predictions
    # predictions = model.predict(x_test)
    # predictions = np.argmax(predictions, axis=1)
    # # print some to screen
    # for x, y, p in zip(x_test, y_test, predictions):
    #    print("x, y, prediction: ", x, y, p)

if __name__ == "__main__":
    DNNTraining()
