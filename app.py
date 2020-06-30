# importing packages
import math
import pandas as pd
import numpy as np
import re
import nltk
from nltk.corpus import stopwords
from preprocess import preprocess
##Creating a list of stop words and adding custom stopwords
stop_words = set(stopwords.words("english"))
import logging
from flask import Flask,Blueprint, flash, redirect, render_template, request, url_for,json,current_app, jsonify


app = Flask(__name__)
logger = logging.getLogger(__name__)


@app.route('/')
def home():
	return render_template('home.html')

@app.route('/predict',methods=['POST'])  
def predict():
    if request.method =='POST':
        my_prediction = preprocess()        
        
    return render_template('result.html',prediction = my_prediction)

@app.route('/results',methods=['POST'])  
def results():
    if request.method =='POST':
        method_prediction = preprocess()  
        responses = jsonify(prediction = method_prediction)
        responses.status_code = 200              
        
    return (responses)


if __name__ == '__main__':
	app.run(host='0.0.0.0',port=8000)









































 







