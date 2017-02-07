"""
Created on Tue Jan 31 13:00:42 2017

@author: Nicki
"""

#%%
import tflearn as tfl
import h5py
import argparse
import numpy as np
from datetime import datetime
import time
#%%
def save_obj(obj, name):
    import pickle as pkl
    with open(name + '.pkl', 'wb') as f:
        pkl.dump(obj, f, pkl.HIGHEST_PROTOCOL)
#%%
def tower_network(reuse = False):
    net = tfl.input_data(shape = (None, 250, 250, 3))
    
    net = tfl.conv_2d(net, 32, 3, strides = 2, activation = 'tanh', reuse = reuse, scope = 'conv1')
    net = tfl.max_pool_2d(net, 2, strides = 2)
    net = tfl.batch_normalization(net)
#    net = tfl.dropout(net, 0.8)
    
    net = tfl.fully_connected(net, 1024, activation = 'tanh', reuse = reuse, scope = 'fc1', regularizer = 'L2')
#    net = tfl.dropout(net, 0.8)
    
    return net
#%%    
def similarity_network(tower1, tower2):
    num_classes = 2
    # Marge layer
    net = tfl.merge([tower1, tower2], mode = 'concat', axis = 1, name = 'Merge')
    
    # Decision network
 #   net = tfl.fully_connected(net, 1024, activation = 'tanh', regularizer = 'L2')
    #net = tfl.dropout(net, 0.5)
#    net = tfl.fully_connected(net, 1024, activation = 'tanh', regularizer = 'L2')
    #net = tfl.dropout(net, 0.5)
    
    # Softmax layer
    net = tfl.fully_connected(net, num_classes, activation = 'softmax')
    
    return net
#%%
if __name__ == '__main__':
    # Parameters
    parser = argparse.ArgumentParser(description='''This program will train a 
                siamese convolutional neural network on the lfw dataset.''')
    parser.add_argument('-at', action="store", dest="augment_type", type = int, default = 0,
                        help = '''Augmentation type. 0=no augmentation, 1=normal augmentation
                                ,2=cpab augmentation''')
    parser.add_argument('-lr', action="store", dest="learning_rate", type=float, default = 0.000001,
                        help = '''Learning rate for optimizer''')
    parser.add_argument('-ne', action="store", dest="num_epochs", type=int, default = 10,
                        help = '''Number of epochs''')
    parser.add_argument('-bs', action="store", dest="batch_size", type=int, default = 100,
                        help = '''Batch size''')
    res = parser.parse_args()
    
    augment_type = res.augment_type
    learning_rate = res.learning_rate
    num_epochs = res.num_epochs
    batch_size = res.batch_size
    print("Fitting siamese network with parameters")
    print("    with augmentation type: " + str(augment_type))
    print("    with learning rate:     " + str(learning_rate))
    print("    with batch size:        " + str(batch_size))  
    print("    in number of epochs:    " + str(num_epochs))
    
    # Load data ....
    if augment_type == 0:
        h5f = h5py.File('lfw_augment_no.h5', 'r')
    elif augment_type == 1:
        h5f = h5py.File('lfw_augment_normal.h5', 'r')
    elif augment_type == 2:
        h5f = h5py.File('lfw_augment_cpab.h5', 'r')
    else:
        ValueError('Set augment type to 0, 1 or 2')
    
    X_train = h5f['X_train']
    y_train = h5f['y_train']
    X_val = h5f['X_val']
    y_val = h5f['y_val']
    X_test = h5f['X_test']
    y_test = h5f['y_test']
    
    # Tower networks
    net1 = tower_network(reuse = False)
    net2 = tower_network(reuse = True)
    
    # Similarity network
    net = similarity_network(net1, net2)
    
    # Learning algorithm
    net = tfl.regression(net, 
                         optimizer = 'adam', 
                         learning_rate = learning_rate,
                         loss = 'categorical_crossentropy', 
                         name = 'target')
    
    # Training
    model = tfl.DNN(net, tensorboard_verbose = 0,
                    tensorboard_dir='/home/nicki/Documents/CPAB_data_augmentation/network_res/')
    '''
    tensorboard_verbose:
        0: Loss, Accuracy (Best Speed).
        1: Loss, Accuracy, Gradients.
        2: Loss, Accuracy, Gradients, Weights.
        3: Loss, Accuracy, Gradients, Weights, Activations, Sparsity.(Best visualization)
    '''
    uniq_id = datetime.now().strftime('%Y_%m_%d_%H_%M')
    start_time = time.time()
    model.fit(  [X_train[:,0], X_train[:,1]], tfl.data_utils.to_categorical(y_train,2), 
                validation_set = ([X_val[:,0], X_val[:,1]], tfl.data_utils.to_categorical(y_val,2)),
                n_epoch = num_epochs,
                show_metric = True,
                batch_size = batch_size,
                run_id = 'lfw_' + str(augment_type) + '_' + uniq_id)
    end_time = time.time()
    # Do final test evaluation
    score=10*[0]
    for i in range(10):
        score[i] = model.evaluate([X_test[i,:,0], X_test[i,:,1]], tfl.data_utils.to_categorical(y_test[i],2))[0]
    print('Mean test acc.: ', np.mean(score), '+-', np.round(np.std(score),3))
    save_obj({'test_score': score, 'time': end_time - start_time}, 'network_res/' + 'lfw_' + str(augment_type) + '_' + uniq_id)
    
    # Close file
    h5f.close()
