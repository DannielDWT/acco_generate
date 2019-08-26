#!/usr/bin/env python
# encoding: utf-8
'''
@author: 10858
@license: (C) Copyright
@contact: xxx@qq.com
@software: PyCharm
@file: ACC_PARSER_SongWeight.py
@time: 2019-08-24 9:58
@desc:
'''

from music21 import *
import numpy as np
import random
from collections import defaultdict, OrderedDict
from itertools import groupby, zip_longest
from ACCO_GLOBALDATA.ACCO_GLOBALDATA_CNotes import CNotes
from ACCO_GLOBALDATA.ACCO_GLOBALDATA_Chord import CChord


class SongParser_weight:

    def __init__(self, filepath):
        pass

    def parse_training(self, melody, acco):
        '''
        :param melody: 由midi文件解析出的主旋律音轨
        :param acco:  由midi文件解析出的和弦音轨
        :return: 一首歌曲组成的训练样本X与y
        该函数用于解析midi的音轨获得训练样本数据，训练样本的特征结构如上注释
        通过将音轨按小节分组，并统计小节中的各个二音符组合出现的次数, 每次出现在相应组合加上时值和权重乘积，空音符不考虑，进而组成样本数据X
        通过将和弦分组，每一小节中的和弦即为对应的输出。
        （目前存在的问题包括是否要考虑进常用的和弦变化规律以及是否考虑头部尾部C大调的特殊编配原则）
        组合格式如下：
        13, 14, 15, 16, 24, 25, 26, 27, 35, 36, 37, 46, 47, 57
        '''
        X = []
        y = []
        melody_Tuples = [(int(n.offset / 4), n) for n in melody]
        melody_m = 0
        for key_x, group in groupby(melody_Tuples, lambda x: x[0]):
            temp = np.zeros((1, CNotes.notes_num_weight)).tolist()
            sum = 0.0
            for n in group:
                print(n[1].pitch)
                if ((isinstance(n[1], note.Rest)) or (n[1] not in CNotes.CNotes_To_Enum_weight.keys())):
                    continue
                for col in CNotes.CNotes_To_Enum_weight[n[1]]:
                    temp[col] += n[1].quarterLength * CNotes.quarter_weight
                    sum += temp[col]
            #归一化，避免含音符较多的小节获得较大的优势
            temp = [w / sum for w in temp]
            X.append(temp)
            melody_m += 1

        acco_measures = OrderedDict()
        offsetTuples_acco = [(int(n.offset / 4), ch) for ch in acco]
        acco_m = 0
        for key_x, group in groupby(offsetTuples_acco, lambda x: x[0]):
            #if (group.length == 0):
            if (group[0][1] not in CChord.CChord_To_Enum):
                group[0][1] = CChord.Enum_To_CChord[random.randint(0, 6)]
            y.append(CChord.CChord_To_Enum[group[0][1]])
            #acco_measures[acco_m] = [n[1] for n in group]
            acco_m += 1
        return np.mat(X), np.mat(y).transpose()

    def parse_predict(self, melody):
        '''
        :param melody: 预测样本的主旋律
        :return: 返回该首歌解析获得的预测样本
        解析用于预测的主旋律音轨，解析方法与上述一致
        '''
        X = []
        y = []
        melody_Tuples = [(int(n.offset / 4), n) for n in melody]
        melody_m = 0
        for key_x, group in groupby(melody_Tuples, lambda x: x[0]):
            temp = np.zeros((1, CNotes.notes_num)).tolist()
            sum = 0.0
            for n in group:
                print(n[1].pitch)
                if ((isinstance(n[1], note.Rest)) or (n[1] not in CNotes.CNotes_To_Enum_weight.keys())):
                    continue
                for col in CNotes.CNotes_To_Enum_weight[n[1]]:
                    temp[col] += n[1].quarterLength * CNotes.quarter_weight
                    sum += temp[col]
            #归一化，避免含音符较多的小节获得较大的优势
            temp = [w / sum for w in temp]
            X.append(temp)
            melody_m += 1
        return np.mat(X)

    def unparse(self, y):
        '''
        :param y: 预测获得的m * 1维矩阵
        :return: 未加头部的伴奏音轨
        '''
        acco = stream.Stream()
        offset = 0.0
        for value in y:
            acco.insert(offset, CChord.Enum_To_CChord(value))
            offset += 4.0
        return acco


    def parser_header(self, melody):
        '''
        :param melody: 主旋律音轨
        :return:
        获取训练/预测样本的头部信息
        '''
        stream_key = melody.getElementsByClass(key.Key)
        if (isinstance(stream_key, list)):
            self.__stream_key = stream_key[0]
        stream_instrument = melody.getElementsByClass(instrument.Instrument)
        if (isinstance(stream_instrument, list)):
            self.__stream_instrument = stream_instrument[0]
        stream_timeSignature = melody.getElementsByClass(meter.TimeSignature)
        if (isinstance(stream_timeSignature, list)):
            self.__stream_timeSignature = stream_timeSignature[0]
        stream_metronomeMark = melody.getElementsByClass(tempo.MetronomeMark)
        if (isinstance(stream_metronomeMark, list)):
            self.__stream_metronomeMark = stream_metronomeMark[0]

    def remove_header(self, stream_raw):
        '''
        :param stream_raw: 包含头部信息的音轨
        :return: 移除不必要信息的音轨
        '''
        processed_stream = stream.Stream()
        for nr in stream_raw:
            if isinstance(nr, note.Note) or isinstance(nr, note.Rest) or isinstance(nr, chord.Chord):
                processed_stream.insert(nr.offset, nr)
        return processed_stream

    def parser_midi_training(self, filepath):
        midi_stream = converter.parse(filepath)
        return midi_stream[0], midi_stream[1]

    def parser_midi_predict(self, filepath):
        midi_stream = converter.parse(filepath)
        return midi_stream

    def training_join(self, X1, X2, y1, y2):
        '''
        :param X1: 一首歌曲组成的训练样本X1
        :param X2: 一首歌曲组成的训练样本X2
        :param y1: 与X1对应的label
        :param y2: 与x2对应的label
        :return: 合并后的训练数据和label
        '''
        X = np.concatenate([X1, X2])
        y = np.concatenate([y1, y2])
        return X, y