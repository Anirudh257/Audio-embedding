#Train audioset bal_train embedding sequences using a bidirectional LSTM model

from keras.preprocessing.sequence import pad_sequences
from keras.models import Sequential
from keras.layers import Dense, Bidirectional, LSTM, BatchNormalization, Dropout

from sklearn.model_selection import train_test_split
import tensorflow as tf
import numpy as np

#Standard libraries
import glob
import pickle

#Filenames, constants and hyperparameters
CLASS_LABELS_INDICES_FILENAME = "/home/anirudh/Desktop/Unbalanced clapping/unbal_clapping_examples.csv"
LSTM_MODEL_FILENAME = "/home/anirudh/Downloads/67top1acc_bidirectional_lstm_dropout_batchnorm_sgd.h5"
TFRECORD_LOCATION = "/home/anirudh/Desktop/clapping_tf records/"

N_CLASSES = 527

def get_multihot_encoding(x,class_ids = list(range(N_CLASSES))):
    enc = []
    for i in class_ids:
        if i in x:
            enc.append(1)
        else:
            enc.append(0)
    return enc

def get_class_display_names(output_vector,classes2displaynames=None,n_class_indices_to_return=5):
    if classes2displaynames is None:
        with open(CLASS_LABELS_INDICES_FILENAME,"r") as fh:
            allclasses = fh.read().splitlines()
        classes2displaynames = {int(i.split(',')[0]):i.split(',')[2] for i in allclasses[1:]}
        
    #Sort indices according to their size of their values and then reverse the result to obtain
    #class indices in decreasing order of confidence
    return np.argsort(output_vector)[::-1][:n_class_indices_to_return]

def main():
    with open(CLASS_LABELS_INDICES_FILENAME, "r") as fh:
        allclasses = fh.read().splitlines()
    classes2displaynames = {int(i.split(',')[0]):i.split(',')[2] for i in allclasses[1:]}
    
    audio_embeddings_dict = {}
    audio_labels_dict = {}
    audio_multihot_dict = {}
    all_tfrecord_filenames = glob.glob(TFRECORD_LOCATION + "*.tfrecord")
    top_tfrecord_filenames = [TFRECORD_LOCATION + i + '.tfrecord' for i in top_tfrecord_filenames]
    
    #Load embeddings
    sess = tf.Session()
    for tfrecord in top_tfrecord_filenames:
        for example in tf.python_io.tf_record_iterator(tfrecord):
            if len(audio_embeddings_dict) % 200 == 0:
                print("Saving dictionary: {}".format(len(audio_embeddings_dict)))
                pickle.dump(audio_embeddings_dict, open('audio_embeddings_dict_bal_train_{}.pkl'.format(len(audio_embeddings_dict)),'wb'))
                pickle.dump(audio_multihot_dict, open('audio_multihot_dict_bal_train_{},pkl'.format(len(audio_multihot_dict)),'wb'))
            tf_example = tf.train.Example.FromString(example)
            vid_id = tf_example.features.feature['video_id'].bytes_list.value[0].decode(encoding = 'UTF-8')
            
            example_label = list(np.asarray(tf_example.features.feature['labels'].int64_list.value))
            tf_seq_example = tf.train.SequenceExample.FromString(example)
            n_frames = len(tf_seq_example.feature_lists.feature_list['audio_embedding'].feature)
            audio_frame = []
            for i in range(n_frames):
                    audio_frame.append(tf.cast(tf.decode_raw(tf_seq_example.feature_lists.feature_list['audio_embedding'].feature[i].bytes_list.value[0],tf.unit8),tf.float32 ).eval(session = sess))
            audio_embeddings_dict[vid_id] = audio_frame
            audio_labels_dict[vid_id] = example_label
            audio_multihot_dict[vid_id] = get_multihot_encoding(example_label)
        if len(audio_embeddings_dict) % 200 ==0:
            print("Saving dictionary: {}".format(len(audio_embeddings_dict)))
            pickle.dump(audio_embeddings_dict, open('audio_embeddings_dict_bal_train_{}.pkl'.format(len(audio_embeddings_dict)),'wb'))
            pickle.dump(audio_multihot_dict, open('audio_multihot_dict_bal_train_{}.pkl'.format(len(audio_multihot_dict)),'wb'))
            
    #Train-test split
    train, test = train_test_split(list(audio_labels_dict.keys()))
    xtrain = [audio_embeddings_dict[k] for k in train]
    ytrain = [audio_multihot_dict[k] for k in train]
    
    xtest = [audio_embeddings_dict[k] for k in test]
    ytest = [audio_multihot_dict[k] for k in test]
    
    #Pad all inputs to have constant sequence length
    maxlen = 10
    x_train = pad_sequences(xtrain, maxlen = maxlen)
    x_test = pad_sequences(xtest, maxlen = maxlen)
    
    y_train = np.asarray(ytrain)
    y_test = np.asarray(ytest)
    
    #Define sequential model in Keras
    print('Building model...')
    
    model = Sequential()
    model.add(BatchNormalization(input_shape = (maxlen, 128)))
    model.add(Dropout(.5))
    model.add(Bidirectional(LSTM(128, init = 'normal', activation = 'relu')))
    model.add(Dense(N_CLASSES,activation = 'sigmoid', init = 'normal'))
    
    #Try using different optimizers and different optimizer configs
    model.compile(loss = 'binary_crossentropy',optimizer = 'adam', metrics = ['accuracy'])
    
    #Train sequential model
    print('Train...')
    
    model.fit(x_train, y_train, batch_size = BATCH_SIZE_, nb_epoch = NB_EPOCH, validation_data = (x_test, y_test))
    model.save(LSTM_MODEL_FILENAME, overwrite = True)
    
    #Get test set accuracy
    score, acc = model.evaluate(x_test,y_test,batch_size = 64)
    print('Test score:', score)
    print('Test accuracy', acc)
    
if __name__ == "main":
    main()
            
            
            
            
