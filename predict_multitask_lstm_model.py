# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author : WenRichard
# @Email : RichardXie1205@gmail.com
# @File : test_lstm_crf.py
# @Software: PyCharm

import logging
import tensorflow as tf
import numpy as np
import pickle
import datetime
import re
import time

# 在这里加载不同的casecade_model
from model_multitask_lstm import MyModel
from public_tools.data_preprocess_multitask import read_corpus, load_vocab, load_tag2label, load_attr2label, batch_yield, pad_sequences, sentence2id
from public_tools.ner_utils import get_entity_without_labelid, trans_label
from tensorflow.python.util import compat

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Parameters
# ==================================================

# Data loading params
tf.flags.DEFINE_string("train_data_file", "./data/resume_ner/train.txt", "Data source for the train data.")
tf.flags.DEFINE_string("test_data_file", "./data/resume_ner/test.txt", "Data source for the test data.")
tf.flags.DEFINE_string("char_vocab_file", "./data/vocab_cn.txt", "bert char vocab.")
tf.flags.DEFINE_string("tag2label_file", "./data/resume_ner/multitask/bmeo2label.txt", "bmeo2label dic.")
tf.flags.DEFINE_string("attr2label_file", "./data/resume_ner/multitask/attr2label.txt", "attr2label dic.")

# Model path
tf.flags.DEFINE_string("model_ckpt_path", 'D:/Expriment/model_output/ner_tool/lstm_crf/multi_task/resume_ner/runs/1620634170/checkpoints', "ckpt model path.")

# Model Hyperparameters
tf.flags.DEFINE_integer("embedding_dim", 768, "Dimensionality of character embedding (default: 128)")
tf.flags.DEFINE_string("filter_sizes", "3,4,5", "Comma-separated filter sizes (default: '3,4,5')")
tf.flags.DEFINE_integer("num_filters", 256, "Number of filters per filter size (default: 128)")
tf.flags.DEFINE_integer("max_length", 160, "Length of sentence (default: 160)")
tf.flags.DEFINE_float("dropout_keep_prob", 0.5, "Dropout keep probability (default: 0.5)")
tf.flags.DEFINE_float("l2_reg_lambda", 0.0, "L2 regularization lambda (default: 0.0)")
tf.flags.DEFINE_float("learning_rate", 1e-3, "Learning rate (default: 0.001)")
tf.flags.DEFINE_float("clip_grade", 5.0, "clip_grad (default: 5.0)")

# Training parameters
tf.flags.DEFINE_integer("batch_size", 128, "Batch Size (default: 64)")
tf.flags.DEFINE_integer("num_epochs", 30, "Number of training epochs (default: 200)")
tf.flags.DEFINE_integer("evaluate_every", 100, "Evaluate model on dev set after this many steps (default: 100)")
tf.flags.DEFINE_integer("checkpoint_every", 100, "Save model after this many steps (default: 100)")
tf.flags.DEFINE_integer("num_checkpoints", 5, "Number of checkpoints to store (default: 5)")

# Misc Parameters
tf.flags.DEFINE_boolean("allow_soft_placement", True, "Allow device soft device placement")
tf.flags.DEFINE_boolean("log_device_placement", False, "Log placement of ops on devices")
tf.flags.DEFINE_boolean("use_clip_grad", False, "clip grad")


tf.flags.DEFINE_string('model_version', '1', 'version number of the model.')
FLAGS = tf.flags.FLAGS


# Data Preparation
# ==================================================


# Load data
print("Loading data...")
char2id, id2char = load_vocab(FLAGS.char_vocab_file)
bmeo2id, id2bmeo = load_tag2label(FLAGS.tag2label_file)
attr2id, id2attr = load_attr2label(FLAGS.attr2label_file)


# Load embeddings
with open('./embedding/new_bert_embedding.pkl', 'rb') as f:
    char_embeddings = pickle.load(f)


def dev_by_ckpt():
    model = MyModel(embedding_dim=768,
                    hidden_dim=300,
                    vocab_size_char=len(char2id),
                    vocab_size_bmeo=len(bmeo2id),
                    vocab_size_attr=len(attr2id),
                    O_tag_index=bmeo2id["O"],
                    use_crf=False,
                    embeddings=char_embeddings,
                    )
    sess = tf.Session()
    sess.run(tf.global_variables_initializer())
    saver = tf.train.Saver()
    ckpt = tf.train.get_checkpoint_state(FLAGS.model_ckpt_path)
    if ckpt is None:
        print ('Model not found, please train your model first')
    else:
        path = ckpt.model_checkpoint_path
        print ('loading pre-trained model from %s.....' % path)
        saver.restore(sess, path)
    return sess, model


def predict_offline():
    pass


def get_result(sess, model):
    while True:
        raw_text = input("Enter your input: ")
        # text = '黄晨担任交通银行行长'
        text = re.split(u'[，。！？、‘’“”（）]', raw_text)
        print('text:')
        print(text)

        # data
        seqs = []
        for sent in text:
            sent_ = sentence2id(sent, char2id)
            seqs.append(sent_)

        seq_list, seq_len_list = pad_sequences(seqs, max_len=FLAGS.max_length)
        feed_dict = {
            model.input_x: seq_list,
            model.input_x_len: seq_len_list,
            model.dropout_keep_prob: 1.0,
            model.lr: FLAGS.learning_rate,
        }
        time_start = datetime.datetime.now()
        (preds_bmeo, preds_attr) = sess.run(model.outputs, feed_dict)
        preds_bmeo = preds_bmeo.tolist()
        preds_attr = preds_attr.tolist()
        print(
            '每条数据预测时间耗时约：{} ms '.format((datetime.datetime.now() - time_start).microseconds / 1000))

        print(preds_bmeo)
        print(preds_attr)
        pred_sent_label = trans_label(preds_bmeo, preds_attr, id2bmeo, id2attr)
        print(pred_sent_label[0])
        entity = get_entity_without_labelid(text, pred_sent_label)

        print('predict_result:')
        print(entity)

        sent_tag = ' '.join(pred_sent_label[0])
        print(raw_text + '\n' + sent_tag)
        print('entity_result:')
        for i in entity:
            print(i)


if __name__ == '__main__':
    ckpt_sess, ckpt_model = dev_by_ckpt()
    get_result(ckpt_sess, ckpt_model)






