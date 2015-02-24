try:
   import cPickle as pickle
except:
   import pickle


def my_pickle(data, path):
    f = open(path, 'wb')
    pickle.dump(data, f)
    f.close()

def my_unpickle(path):
    f = open(path, 'rb')
    data = pickle.load(f)
    f.close()
    return data

