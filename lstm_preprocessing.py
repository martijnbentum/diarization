import locations
import video_to_flm
import video_info
import tensorflow as tf
from tensorflow.keras.utils import timeseries_dataset_from_array


class Data:
    def __init__(self, train_perc = 70, val_perc = 10, test_perc = 20,
        perc_success = 80,tables = None, label_start_index = 51,
        batch_size = 64, shuffle = True):
        self.train_perc = train_perc
        self.val_perc = val_perc
        self.test_perc = test_perc
        self.perc_success = perc_success
        self.tables = tables
        self.label_start_index = label_start_index
        self.batch_size = batch_size
        self.sequence_length = (label_start_index - 1) * 2 + 1
        self.d = video_info.make_video_infos(tables)
        self.facial_landmarks_info = video_to_flm.analyze_all_facial_landmarks()
        self._select_videos()
        self._split_infos()

    def _select_videos(self):
        self.names = []
        self.excluded_names = []
        for k, v in self.facial_landmarks_info.items():
            if v['perc_success'] >= self.perc_success:
                self.names.append(v['name'])
            else: self.excluded_names.append(v['name'])
        self.video_infos = []
        self.excluded_video_infos = []
        self.no_table_info = []
        for k, info in self.d.items():
            if not info.table: 
                self.no_table_info.append(info)
                continue
            found = False
            for name in self.names:
                if name in k:
                    self.video_infos.append(info)
                    found = True
            if not found:
                self.excluded_video_infos.append(info)

    def _split_infos(self):
        n = len(self.video_infos)
        train = int(n*self.train_perc/100)
        val = int(n*self.val_perc/100) + train
        test = int(n*self.test_perc/100) + val
        self.train_infos = self.video_infos[:train]
        self.val_infos = self.video_infos[train:val]
        self.test_infos = self.video_infos[val:]

    def _make_data(self, name):
        sequence_length = self.sequence_length
        index = self.label_start_index
        if hasattr(self,'_' + name): return getattr(self,'_' + name)
        infos = getattr(self,name + '_infos')
        info = infos[0]
        data = timeseries_dataset_from_array(info.X,
            info.y[index:], sequence_length=sequence_length, 
            batch_size=self.batch_size, shuffle = True)
        for info in infos[1:]:
            print(info)
            data = data.concatenate(timeseries_dataset_from_array(info.X, 
                info.y[index:], sequence_length=sequence_length, 
                batch_size=self.batch_size, shuffle = True))
        setattr(self,'_' + name,data)
        return getattr(self,'_' + name)

    @property
    def train(self):
        return self._make_data('train')

    @property
    def val(self):
        return self._make_data('val')

    @property
    def test(self):
        return self._make_data('test')
    
    def save(self):
        self.train.save(locations.lstm_train_data)
        self.val.save(locations.lstm_val_data)
        self.test.save(locations.lstm_test_data)


        
