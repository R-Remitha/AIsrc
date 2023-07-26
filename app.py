from flask import Flask, flash, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL
from flask_session import Session
from config import app
from wxconv import WXC
import MySQLdb.cursors
import re
from config import mysql
import os
import json
from flask_cors import CORS, cross_origin

# from client.src.Navigation import login
# from flask_restx import Api, Resource, fields
# import jwt
# from .models import db, Users
# from flask_restx import Api, Resource, fields
# import jwt
# from .models import db, Users

Session(app)
CORS(app)
auth_id = 0
dis_id = 0

# http://127.0.0.1:9999/एक शेर जंगल में सो रहा था। वो चूहे पर बहुत गुस्सा करता है। चूहा उससे विनती करता है कि वह उसे जाने दे। एक दिन वह उसकी सहायता करेगा। चूहे की बात सुनकर शेर हंसता है। एक दिन वह उसकी सहायता करेगा।
# @app.route('/')
# def index():
#     cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#     cursor.execute("CREATE TABLE IF NOT EXISTS author (author_id int AUTO_INCREMENT , author_name varchar(255), email varchar(255), password varchar(16), reviewer_role varchar(255), PRIMARY KEY(author_id))")
#     cursor.execute("CREATE TABLE IF NOT EXISTS discourse (discourse_id int NOT NULL AUTO_INCREMENT, discourse_name varchar(255),author_id int, no_sentences int, domain varchar(255), create_date datetime default now(), other_attributes VARCHAR(255), sentences MEDIUMTEXT,PRIMARY KEY (discourse_id),FOREIGN KEY (author_id) REFERENCES author(author_id))")
#     cursor.execute("CREATE TABLE IF NOT EXISTS usr (author_id int,  discourse_id int, sentence_id varchar(255) ,USR_ID int NOT NULL AUTO_INCREMENT, orignal_USR_json MEDIUMTEXT,final_USR json,create_date datetime default now(),USR_status varchar(255),FOREIGN KEY (discourse_id) REFERENCES discourse(discourse_id),FOREIGN KEY (author_id) REFERENCES author(author_id), PRIMARY KEY (USR_ID))")
#     cursor.execute(
#         "CREATE TABLE IF NOT EXISTS demlo(demlo_id int AUTO_INCREMENT, demlo_txt JSON, PRIMARY KEY (demlo_id))")
#     mysql.connection.commit()
#     return jsonify(message='all good!')


@app.route('/')
def index():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("CREATE TABLE IF NOT EXISTS author (author_id int AUTO_INCREMENT , author_name varchar(255), email varchar(255), password varchar(16), reviewer_role varchar(255), PRIMARY KEY(author_id))")
    cursor.execute("CREATE TABLE IF NOT EXISTS discourse (discourse_id int NOT NULL AUTO_INCREMENT, discourse_name varchar(255),author_id int, no_sentences int, domain varchar(255), create_date datetime default now(), other_attributes VARCHAR(255), sentences MEDIUMTEXT,PRIMARY KEY (discourse_id),FOREIGN KEY (author_id) REFERENCES author(author_id))")
    cursor.execute("CREATE TABLE IF NOT EXISTS usr (author_id int,  discourse_id int, sentence_id varchar(255) ,USR_ID int NOT NULL AUTO_INCREMENT, orignal_USR_json MEDIUMTEXT,final_USR json,create_date datetime default now(),USR_status varchar(255),FOREIGN KEY (discourse_id) REFERENCES discourse(discourse_id),FOREIGN KEY (author_id) REFERENCES author(author_id), PRIMARY KEY (USR_ID))")
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS demlo(demlo_id int AUTO_INCREMENT, demlo_txt JSON, PRIMARY KEY (demlo_id))")
    # cursor.execute("DROP TABLE edit")
    cursor.execute("CREATE TABLE IF NOT EXISTS edit(edit_id int AUTO_INCREMENT, edited_USR MEDIUMTEXT, edit_date datetime default now(), author_id int,  discourse_id int, USR_ID int, FOREIGN KEY (author_id) REFERENCES author(author_id),FOREIGN KEY (discourse_id) REFERENCES discourse(discourse_id), FOREIGN KEY (USR_ID) REFERENCES usr(USR_ID), status varchar(255), PRIMARY KEY(edit_id), sent_id varchar(255))")
    mysql.connection.commit()
    return "Created"


@app.route('/api/signup/', methods=['POST'])
@cross_origin()
def signup():
    data = json.loads(request.data)
    author_name = data.get('author_name')
    email = data.get('email')
    password = data.get('password')
    reviewer_role = data.get('reviewer_role')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT author_id FROM author WHERE email = %s and reviewer_role=%s', (email, reviewer_role))
    author = cursor.fetchone()
    if author is not None:
        return jsonify(message='Author already exists!'), 409
    elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
        return jsonify(message='Invalid email address!'), 400
    else:
        cursor.execute('INSERT INTO author VALUES (NULL, %s, %s, %s, %s)', (author_name, email, password, reviewer_role))
        mysql.connection.commit()
        return jsonify(message='You have successfully registered!'), 200


@app.route('/api/login/', methods=['GET', 'POST'])
def login():
    global auth_id
    if request.method == 'POST':
        data = json.loads(request.data)
        email = data.get('email')
        password = data.get('password')
        reviewer_role = data.get('reviewer_role')
        if reviewer_role == 'author':
            reviewer_role_value = 'No'
        elif reviewer_role == 'reviewer':
            reviewer_role_value = 'Yes'
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM author WHERE email = % s AND password = % s ', (email, password))
        author = cursor.fetchone()
        if author:
            auth_id = author['author_id']
            session['loggedIn']=True
            session['author_id']=auth_id
            if reviewer_role_value == 'No' and author['reviewer_role'] == 'No':
                msg = 'Logged in successfully!'
                return jsonify({'message': msg}), 200
            elif reviewer_role_value == 'Yes' and author['reviewer_role'] == 'Yes':
                msg = 'Logged in successfully!'
                return jsonify({'message': msg}), 201
            elif reviewer_role_value == 'Yes' and author['reviewer_role'] == 'No':
                msg = 'Not successfully!'
                return jsonify({'message': msg}), 202
            elif reviewer_role_value == 'No' and author['reviewer_role'] == 'Yes':
                msg = 'Logged in successfully!'
                return jsonify({'message': msg}), 203
        else:
            return jsonify({'error': 'Invalid credentials'}), 401



@app.route('/usrgenerate', methods = ['GET','POST'])
def usrgenerate():
    global dis_id
    if request.method == "POST":
        data = request.get_json()
        sentences = data.get('sentences')
        discourse_name = data.get('discourse_name')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT author_name FROM author WHERE author_id = % s ', (auth_id, ))
        author_id = cursor.fetchone()

        # sent = "एक समय की बात है। एक शेर जंगल में सो रहा था। एक चूहा शेर पर चढ़ कर उछल कूद कर रहा था। शेर की नींद टूट जाती है। वो चूहे पर बहुत गुस्सा करता है। चूहा उससे यह विनती करता है। वह उसे जाने की अनुमति दे। एक दिन वह उसकी सहायता करेगा। चूहे की बात सुनकर शेर हंसता है। कुछ महीने के बाद एक दिन जंगल में शिकारी आते है। वो शेर को पकड़ लेते है। उसे रस्सी से बांध देते है। शेर खुद को छुड़ाने की पूरी कोशिश करता है। वह परेशान होकर ज़ोर से दहाड़ने लगता है।"

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("INSERT INTO discourse(author_id, sentences, discourse_name) VALUES(%s, %s, %s)",(auth_id, sentences, discourse_name))
        mysql.connection.commit()

        row_id = cursor.lastrowid
        dis_id = row_id
        
        print("dis_id from usrgenerate:",dis_id)

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # cursor.execute("INSERT INTO usr(author_id, discourse_id, orignal_USR_json) VALUES(%s, %s, %s)",(auth_id, dis_id, {'Concept': ['eka_1', 'Sera_1', 'jaMgala_1', 'so_1-0_rahA_WA_1'], 'Index': [1, 2, 3, 4], 'SemCateOfNouns': ['', '', '', ''], 'GNP': ['', '[m sg a]', '[m sg a]', ''], 'DepRel': ['2:card', '4:k1', '4:k7p', '0:main'], 'Discourse': ['', '', '', ''], 'SpeakersView': ['', '', '', ''], 'Scope': ['', '', '', ''], 'SentenceType': ['affirmative']}))
        # cursor.execute("INSERT INTO usr(author_id, discourse_id, orignal_USR_json) VALUES(%s, %s, %s)",(auth_id, dis_id, {'Concept': ['eka_1', 'Sera_1', 'jaMgala_1', 'so_1-0_rahA_WA_1'], 'Index': [1, 2, 3, 4], 'SemCateOfNouns': ['', '', '', ''], 'GNP': ['', '[m sg a]', '[m sg a]', ''], 'DepRel': ['2:card', '4:k1', '4:k7p', '0:main'], 'Discourse': ['', '', '', ''], 'SpeakersView': ['', '', '', ''], 'Scope': ['', '', '', ''], 'SentenceType': ['affirmative']}))
        # mysql.connection.commit()

        if(sentences == "एक समय की बात है। एक शेर जंगल में सो रहा था। एक चूहा शेर पर चढ़ कर उछल कूद कर रहा था। शेर की नींद टूट जाती है। वो चूहे पर बहुत गुस्सा करता है। चूहा उससे यह विनती करता है। वह उसे जाने की अनुमति दे। एक दिन वह उसकी सहायता करेगा। चूहे की बात सुनकर शेर हंसता है। कुछ महीने के बाद एक दिन जंगल में शिकारी आते है। वो शेर को पकड़ लेते है। उसे रस्सी से बांध देते है। शेर खुद को छुड़ाने की पूरी कोशिश करता है। वह परेशान होकर ज़ोर से दहाड़ने लगता है।"):
            cursor.execute("INSERT INTO usr(author_id, discourse_id, orignal_USR_json) VALUES(%s, %s, %s)",(auth_id, dis_id, {'Concept': ['eka_1','samaya_1','bAwa_1','hE_1-pres'], 'Index': [1, 2, 3, 4], 'SemCateOfNouns': ['', '', '', ''], 'GNP': ['', '[m sg a]', '', '[f sg a]'], 'DepRel': ['2:card','3:r6','4:k1','0:main'], 'Discourse': ['', '', '', ''], 'SpeakersView': ['', '', '', ''], 'Scope': ['', '', '', ''], 'SentenceType': ['affirmative']}))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['eka_1','samaya_1','bAwa_1','hE_1-pres'], 'Index': [1, 2, 3, 4], 'SemCateOfNouns': ['', '', '', ''], 'GNP': ['', '[m sg a]', '', '[f sg a]'], 'DepRel': ['2:card','3:r6','4:k1','0:main'], 'Discourse': ['', '', '', ''], 'SpeakersView': ['', '', '', ''], 'Scope': ['', '', '', ''], 'SentenceType': ['affirmative']}, "In Edit", '1'))
            mysql.connection.commit()
            cursor.execute("INSERT INTO usr(author_id, discourse_id, orignal_USR_json) VALUES(%s, %s, %s)",(auth_id, dis_id, {'Concept': ['eka_1','Sera_1','jaMgala_1','so_1-0_rahA_WA_1'], 'Index': [1, 2, 3, 4], 'SemCateOfNouns': ['', '', '', ''], 'GNP': ['', '[m sg a]', '[m sg a]', ''], 'DepRel': ['2:card', '4:k1', '4:k7p', '0:main'], 'Discourse': ['', '', '', ''], 'SpeakersView': ['', '', '', ''], 'Scope': ['', '', '', ''], 'SentenceType': ['affirmative']}))
            mysql.connection.commit()
            cursor.execute("INSERT INTO usr(author_id, discourse_id, orignal_USR_json) VALUES(%s, %s, %s)",(auth_id, dis_id, {'Concept': ['eka_1','cUhA_1','Sera_1','caDZa_1','uCala_1','kUxa_1-0_rahA_WA_1'], 'Index': [1, 2, 3, 4,5,6], 'SemCateOfNouns': ['', '', '', '','',''], 'GNP': ['','[m sg a]','[m sg a]','','[- - -]',''], 'DepRel': ['3:card','3:mod','4:k7','6:vmod','6:vmod','0:main'], 'Discourse': ['', '', '', '','',''], 'SpeakersView': ['', '', '', '','',''], 'Scope': ['', '', '', '','',''], 'SentenceType': ['affirmative']}))
            mysql.connection.commit()
            cursor.execute("INSERT INTO usr(author_id, discourse_id, orignal_USR_json) VALUES(%s, %s, %s)",(auth_id, dis_id, {'Concept': ['Sera_1','nIMxa_1','tUta_1-wA_hE_1'], 'Index': [1, 2, 3], 'SemCateOfNouns': ['', '', ''], 'GNP': ['[m sg a]','[f sg a]',''], 'DepRel': ['2:r6','3:k1','0:main'], 'Discourse': ['', '', ''], 'SpeakersView': ['', '', ''], 'Scope': ['', '', ''], 'SentenceType': ['affirmative']}))
            mysql.connection.commit()
            cursor.execute("INSERT INTO usr(author_id, discourse_id, orignal_USR_json) VALUES(%s, %s, %s)",(auth_id, dis_id, {'Concept': ['vaha', 'cUhA_1', 'bahuwa_1', 'gussA+kara_1-wA_hE_1'], 'Index': [1, 2, 3, 4], 'SemCateOfNouns': ['', '', '', ''], 'GNP': ['[- sg a]', '[m pl a]', '', ''], 'DepRel': ['2:nmod__adj', '4:k7', '4:nmod__adj', '0:main'], 'Discourse': ['', '', '', ''], 'SpeakersView': ['', '', '', ''], 'Scope': ['', '', '', ''], 'SentenceType': ['affirmative']}))
            mysql.connection.commit()
            cursor.execute("INSERT INTO usr(author_id, discourse_id, orignal_USR_json) VALUES(%s, %s, %s)",(auth_id, dis_id, {'Concept': ['cUhA_1','vaha','yaha','vinawI+kara_1-wA_hE_1'], 'Index': [1, 2, 3, 4], 'SemCateOfNouns': ['', '', '', ''], 'GNP': ['[m sg a]','[- sg a]','',''], 'DepRel': ['4:k1','4:k2','4:nmod__adj','0:main'], 'Discourse': ['', '', '', ''], 'SpeakersView': ['', '', '', ''], 'Scope': ['', '', '', ''], 'SentenceType': ['affirmative']}))
            mysql.connection.commit()
            cursor.execute("INSERT INTO usr(author_id, discourse_id, orignal_USR_json) VALUES(%s, %s, %s)",(auth_id, dis_id, {'Concept': ['vaha','vaha','jAna_1-yA_1','anumawi+xe_1-yA_1'], 'Index': [1, 2, 3, 4], 'SemCateOfNouns': ['', '', '', ''], 'GNP': ['[- sg a]','[- sg a]','',''], 'DepRel': ['3:k2','3:k2','4:k2','0:main'], 'Discourse': ['', '', '', ''], 'SpeakersView': ['', '', '', ''], 'Scope': ['', '', '', ''], 'SentenceType': ['affirmative']}))
            mysql.connection.commit()
            cursor.execute("INSERT INTO usr(author_id, discourse_id, orignal_USR_json) VALUES(%s, %s, %s)",(auth_id, dis_id, {'Concept': ['eka_1','xina_1','vaha','vaha','sahAyawA+kara_1-gA_1'], 'Index': [1, 2, 3, 4,5], 'SemCateOfNouns': ['', 'per', '', '',''], 'GNP': ['','[m sg a]','[- sg a]','[- sg a]',''], 'DepRel': ['2:card','5:k7t','5:k2','5:k2','0:main'], 'Discourse': ['', '', '', '',''], 'SpeakersView': ['', '', '', '',''], 'Scope': ['', '', '', '',''], 'SentenceType': ['affirmative']}))
            mysql.connection.commit()
            cursor.execute("INSERT INTO usr(author_id, discourse_id, orignal_USR_json) VALUES(%s, %s, %s)",(auth_id, dis_id, {'Concept': ['cUhA_1','bAwa_1','suna_1','Sera_1','haMsa_1-wA_hE_1'], 'Index': [1, 2, 3, 4,5], 'SemCateOfNouns': ['','','per','',''], 'GNP': ['[m pl a]','[f sg a]','','[m sg a]',''], 'DepRel': ['2:r6','3:k2','5:vmod','5:k1','0:main'], 'Discourse': ['', '', '', '',''], 'SpeakersView': ['', '', '', '',''], 'Scope': ['', '', '', '',''], 'SentenceType': ['affirmative']}))
            mysql.connection.commit()
            cursor.execute("INSERT INTO usr(author_id, discourse_id, orignal_USR_json) VALUES(%s, %s, %s)",(auth_id, dis_id, {'Concept': ['kuCa_1','mahInA_1','bAxa_1','eka_1','xina_1','jaMgala_1','SikArI_1','A_1-pres'], 'Index': [1, 2, 3, 4,5,6,7,8], 'SemCateOfNouns': ['','','','','per','','',''], 'GNP': ['','[m pl a]','','','[m sg a]','[m sg a]','[m sg a]',''], 'DepRel': ['2:nmod__adj','8:k7t','2:lwg__psp','5:card','8:k7t','8:k7p','8:k1','0:main'], 'Discourse': ['', '', '', '','','','',''], 'SpeakersView': ['', '', '', '','','','',''], 'Scope': ['', '', '', '','','','',''], 'SentenceType': ['affirmative']}))
            mysql.connection.commit()
            cursor.execute("INSERT INTO usr(author_id, discourse_id, orignal_USR_json) VALUES(%s, %s, %s)",(auth_id, dis_id, {'Concept': ['vaha','Sera_1','pakadZa_1-pres'], 'Index': [1, 2, 3], 'SemCateOfNouns': ['','',''], 'GNP': ['[- sg a]','[m sg a]',''], 'DepRel': ['2:nmod__adj','3:k2','0:main'], 'Discourse': ['', '', ''], 'SpeakersView': ['', '', ''], 'Scope': ['', '', ''], 'SentenceType': ['affirmative']}))
            mysql.connection.commit()
            cursor.execute("INSERT INTO usr(author_id, discourse_id, orignal_USR_json) VALUES(%s, %s, %s)",(auth_id, dis_id, {'Concept': ['vaha','rassI_1','bAMXa_1-pres'], 'Index': [1, 2, 3], 'SemCateOfNouns': ['','',''], 'GNP': ['[- sg a]','[f sg a]',''], 'DepRel': ['3:k2','3:k3','0:main'], 'Discourse': ['', '', ''], 'SpeakersView': ['', '', ''], 'Scope': ['', '', ''], 'SentenceType': ['affirmative']}))
            mysql.connection.commit()
            cursor.execute("INSERT INTO usr(author_id, discourse_id, orignal_USR_json) VALUES(%s, %s, %s)",(auth_id, dis_id, {'Concept': ['Sera_1','Kuxa','CudZA_1-yA_1','pUrA_1','koSiSa+kara_1-wA_hE_1'], 'Index': [1, 2, 3,4,5], 'SemCateOfNouns': ['','','','',''], 'GNP': ['[m sg a]','','','',''], 'DepRel': ['5:k1','3:k2','5:k2','5:mod','0:main'], 'Discourse': ['', '', '','',''], 'SpeakersView': ['', '', '','',''], 'Scope': ['', '', '','',''], 'SentenceType': ['affirmative']}))
            mysql.connection.commit()
            cursor.execute("INSERT INTO usr(author_id, discourse_id, orignal_USR_json) VALUES(%s, %s, %s)",(auth_id, dis_id, {'Concept': ['vaha','pareSAna+ho_1','jZora_1','xahAdZa_1-wA_hE_1'], 'Index': [1, 2, 3,4], 'SemCateOfNouns': ['','','',''], 'GNP': ['[- sg a]','','',''], 'DepRel': ['4:k1','4:vmod','4:adv','0:main'], 'Discourse': ['', '', '',''], 'SpeakersView': ['', '', '',''], 'Scope': ['', '', '',''], 'SentenceType': ['affirmative']}))
            mysql.connection.commit()
           
           
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['eka_1','Sera_1','jaMgala_1','so_1-0_rahA_WA_1'], 'Index': [1, 2, 3, 4], 'SemCateOfNouns': ['', '', '', ''], 'GNP': ['', '[m sg a]', '[m sg a]', ''], 'DepRel': ['2:card', '4:k1', '4:k7p', '0:main'], 'Discourse': ['', '', '', ''], 'SpeakersView': ['', '', '', ''], 'Scope': ['', '', '', ''], 'SentenceType': ['affirmative']}, "In Edit", '2'))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['eka_1','cUhA_1','Sera_1','caDZa_1','uCala_1','kUxa_1-0_rahA_WA_1'], 'Index': [1, 2, 3, 4,5,6], 'SemCateOfNouns': ['', '', '', '','',''], 'GNP': ['','[m sg a]','[m sg a]','','[- - -]',''], 'DepRel': ['3:card','3:mod','4:k7','6:vmod','6:vmod','0:main'], 'Discourse': ['', '', '', '','',''], 'SpeakersView': ['', '', '', '','',''], 'Scope': ['', '', '', '','',''], 'SentenceType': ['affirmative']}, "In Edit", '3'))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['Sera_1','nIMxa_1','tUta_1-wA_hE_1'], 'Index': [1, 2, 3], 'SemCateOfNouns': ['', '', ''], 'GNP': ['[m sg a]','[f sg a]',''], 'DepRel': ['2:r6','3:k1','0:main'], 'Discourse': ['', '', ''], 'SpeakersView': ['', '', ''], 'Scope': ['', '', ''], 'SentenceType': ['affirmative']}, "In Edit", '4'))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['vaha', 'cUhA_1', 'bahuwa_1', 'gussA+kara_1-wA_hE_1'], 'Index': [1, 2, 3, 4], 'SemCateOfNouns': ['', '', '', ''], 'GNP': ['[- sg a]', '[m pl a]', '', ''], 'DepRel': ['2:nmod__adj', '4:k7', '4:nmod__adj', '0:main'], 'Discourse': ['', '', '', ''], 'SpeakersView': ['', '', '', ''], 'Scope': ['', '', '', ''], 'SentenceType': ['affirmative']}, "In Edit", '5'))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['cUhA_1','vaha','yaha','vinawI+kara_1-wA_hE_1'], 'Index': [1, 2, 3, 4], 'SemCateOfNouns': ['', '', '', ''], 'GNP': ['[m sg a]','[- sg a]','',''], 'DepRel': ['4:k1','4:k2','4:nmod__adj','0:main'], 'Discourse': ['', '', '', ''], 'SpeakersView': ['', '', '', ''], 'Scope': ['', '', '', ''], 'SentenceType': ['affirmative']}, "In Edit", '6'))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['vaha','vaha','jAna_1-yA_1','anumawi+xe_1-yA_1'], 'Index': [1, 2, 3, 4], 'SemCateOfNouns': ['', '', '', ''], 'GNP': ['[- sg a]','[- sg a]','',''], 'DepRel': ['3:k2','3:k2','4:k2','0:main'], 'Discourse': ['', '', '', ''], 'SpeakersView': ['', '', '', ''], 'Scope': ['', '', '', ''], 'SentenceType': ['affirmative']}, "In Edit", '7'))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['eka_1','xina_1','vaha','vaha','sahAyawA+kara_1-gA_1'], 'Index': [1, 2, 3, 4,5], 'SemCateOfNouns': ['', 'per', '', '',''], 'GNP': ['','[m sg a]','[- sg a]','[- sg a]',''], 'DepRel': ['2:card','5:k7t','5:k2','5:k2','0:main'], 'Discourse': ['', '', '', '',''], 'SpeakersView': ['', '', '', '',''], 'Scope': ['', '', '', '',''], 'SentenceType': ['affirmative']}, "In Edit", '8'))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['cUhA_1','bAwa_1','suna_1','Sera_1','haMsa_1-wA_hE_1'], 'Index': [1, 2, 3, 4,5], 'SemCateOfNouns': ['','','per','',''], 'GNP': ['[m pl a]','[f sg a]','','[m sg a]',''], 'DepRel': ['2:r6','3:k2','5:vmod','5:k1','0:main'], 'Discourse': ['', '', '', '',''], 'SpeakersView': ['', '', '', '',''], 'Scope': ['', '', '', '',''], 'SentenceType': ['affirmative']}, "In Edit", '9'))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id,  {'Concept': ['kuCa_1','mahInA_1','bAxa_1','eka_1','xina_1','jaMgala_1','SikArI_1','A_1-pres'], 'Index': [1, 2, 3, 4,5,6,7,8], 'SemCateOfNouns': ['','','','','per','','',''], 'GNP': ['','[m pl a]','','','[m sg a]','[m sg a]','[m sg a]',''], 'DepRel': ['2:nmod__adj','8:k7t','2:lwg__psp','5:card','8:k7t','8:k7p','8:k1','0:main'], 'Discourse': ['', '', '', '','','','',''], 'SpeakersView': ['', '', '', '','','','',''], 'Scope': ['', '', '', '','','','',''], 'SentenceType': ['affirmative']}, "In Edit", '10'))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['vaha','Sera_1','pakadZa_1-pres'], 'Index': [1, 2, 3], 'SemCateOfNouns': ['','',''], 'GNP': ['[- sg a]','[m sg a]',''], 'DepRel': ['2:nmod__adj','3:k2','0:main'], 'Discourse': ['', '', ''], 'SpeakersView': ['', '', ''], 'Scope': ['', '', ''], 'SentenceType': ['affirmative']}, "In Edit", '11'))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['vaha','rassI_1','bAMXa_1-pres'], 'Index': [1, 2, 3], 'SemCateOfNouns': ['','',''], 'GNP': ['[- sg a]','[f sg a]',''], 'DepRel': ['3:k2','3:k3','0:main'], 'Discourse': ['', '', ''], 'SpeakersView': ['', '', ''], 'Scope': ['', '', ''], 'SentenceType': ['affirmative']}, "In Edit", '12'))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['Sera_1','Kuxa','CudZA_1-yA_1','pUrA_1','koSiSa+kara_1-wA_hE_1'], 'Index': [1, 2, 3,4,5], 'SemCateOfNouns': ['','','','',''], 'GNP': ['[m sg a]','','','',''], 'DepRel': ['5:k1','3:k2','5:k2','5:mod','0:main'], 'Discourse': ['', '', '','',''], 'SpeakersView': ['', '', '','',''], 'Scope': ['', '', '','',''], 'SentenceType': ['affirmative']}, "In Edit", '13'))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['vaha','pareSAna+ho_1','jZora_1','xahAdZa_1-wA_hE_1'], 'Index': [1, 2, 3,4], 'SemCateOfNouns': ['','','',''], 'GNP': ['[- sg a]','','',''], 'DepRel': ['4:k1','4:vmod','4:adv','0:main'], 'Discourse': ['', '', '',''], 'SpeakersView': ['', '', '',''], 'Scope': ['', '', '',''], 'SentenceType': ['affirmative']}, "In Edit", '14'))
            mysql.connection.commit()

        else:
            cursor.execute("INSERT INTO usr(author_id, discourse_id, orignal_USR_json) VALUES(%s, %s, %s)",(auth_id, dis_id, {'Concept': ['addressee','piCalA_8','aXyAya_1','globa_1','mahawwva_6','paDZa_7-0_cukA_hE_1'], 'Index': [1, 2, 3,4,5,6], 'SemCateOfNouns': ['anim','','','','',''], 'GNP': ['[m sg m]','','[- sg a]','[- sg a]','[- sg a]',''], 'DepRel': ['6:k1','3:mod','6:k7p','5:r6','6:k7','0:main'], 'Discourse': ['', '', '','', '',''], 'SpeakersView': ['respect', '', '','','',''], 'Scope': ['', '', '','','',''], 'SentenceType': ['affirmative']}))
            mysql.connection.commit()
            cursor.execute("INSERT INTO usr(author_id, discourse_id, orignal_USR_json) VALUES(%s, %s, %s)",(auth_id, dis_id, {'Concept': ['globa_1','aXyayana+kara_2','kuCa_1','sImA_6','ho_1-wA_hE_1'], 'Index': [1, 2, 3,4,5], 'SemCateOfNouns': ['','','','',''], 'GNP': ['[- sg a]','','','[- pl a]',''], 'DepRel': ['2:k3','4:r6','4:quant','5:k1','0:main'], 'Discourse': ['', '', '','', ''], 'SpeakersView': ['', '', '','',''], 'Scope': ['', '', '','',''], 'SentenceType': ['affirmative']}))
            mysql.connection.commit()
            cursor.execute("INSERT INTO usr(author_id, discourse_id, orignal_USR_json) VALUES(%s, %s, %s)",(auth_id, dis_id, {'Concept': ['speaker','pUrA_3','pqWvI_1','aXyayana+kara_2','cAha_8-wA_hE_1'], 'Index': [1, 2, 3, 4,5], 'SemCateOfNouns': ['anim', '', '', '',''], 'GNP': ['[- pl u]','','[- sg a]','',''], 'DepRel': ['5:k1','3:mod','4:r6','5:k2','0:main'], 'Discourse': ['', '', '', '',''], 'SpeakersView': ['', '', 'def', '',''], 'Scope': ['', '', '', '',''], 'SentenceType': ['affirmative']}))
            mysql.connection.commit()
            cursor.execute("INSERT INTO usr(author_id, discourse_id, orignal_USR_json) VALUES(%s, %s, %s)",(auth_id, dis_id, {'Concept': ['globa_1','speaker','kAPI_1','upayogI_1','sAbiwa+ho_1-wA_hE_1'], 'Index': [1, 2, 3, 4,5], 'SemCateOfNouns': ['', 'anim', '', '',''], 'GNP': ['[- sg a]','[- pl u]','','',''], 'DepRel': ['5:k1','5:rt','4:intf','5:k2','0:main'], 'Discourse': ['','','','','Geo_ncert_6stnd_4ch_0003a.5:conditional'], 'SpeakersView': ['', '', '', '',''], 'Scope': ['', '', '', '',''], 'SentenceType': ['affirmative']}))
            mysql.connection.commit()
            cursor.execute("INSERT INTO usr(author_id, discourse_id, orignal_USR_json) VALUES(%s, %s, %s)",(auth_id, dis_id, {'Concept': ['speaker','pqWvI','eka_1','BAga_2','apanA','xeSa_1','rAjya_7','jilA_3','Sahara_2','gAzva_1','aXyayana+kara_2,cAha_8-wA_hE_1'], 'Index': [1, 2, 3, 4,5,6,7,8,9,10,11,12], 'SemCateOfNouns': ['anim','','','','','','','','','','',''], 'GNP': ['[- pl u]','[- sg a]','','[- sg a]','','[- sg a]','[- pl a]','[- pl a]','[- pl a]','[- pl a]','',''], 'DepRel': ['12:k1','4:r6','4:card','11:k7','6:r6','4:re','4:re','4:re','4:re','4:re','12:k2','0:main'], 'Discourse': ['','','','','1:coref','','','','','','',''], 'SpeakersView': ['','','kevala','','','','','','','','',''], 'Scope': ['', '', '', '','','','','','','','',''], 'SentenceType': ['affirmative']}))
            mysql.connection.commit()
            cursor.execute("INSERT INTO usr(author_id, discourse_id, orignal_USR_json) VALUES(%s, %s, %s)",(auth_id, dis_id, {'Concept': ['yaha','speaker','uwanA_1','upayogI_1','nahIM_1','sAbiwa+ho_1-wA_hE_1'], 'Index': [1, 2, 3, 4,5,6], 'SemCateOfNouns': ['','','','','',''], 'GNP': ['[- sg a]','[- pl u]','','','',''], 'DepRel': ['5:k1','5:rt','4:intf','5:k2','5:neg','0:main'], 'Discourse': ['Geo_ncert_6stnd_4ch_0004a.12:coref','','','','Geo_ncert_6stnd_4ch_0003b.6:contrast', 'Geo_ncert_6stnd_4ch_0004a.12:conditional'], 'SpeakersView': ['','','','','',''], 'Scope': ['','','','','',''], 'SentenceType': ['negative']}))
            mysql.connection.commit()

            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['eka_1','Sera_1','jaMgala_1','so_1-0_rahA_WA_1'], 'Index': [1, 2, 3, 4], 'SemCateOfNouns': ['', '', '', ''], 'GNP': ['', '[m sg a]', '[m sg a]', ''], 'DepRel': ['2:card', '4:k1', '4:k7p', '0:main'], 'Discourse': ['', '', '', ''], 'SpeakersView': ['', '', '', ''], 'Scope': ['', '', '', ''], 'SentenceType': ['affirmative']}, "In Edit", "2"))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['eka_1','cUhA_1','Sera_1','caDZa_1','uCala_1','kUxa_1-0_rahA_WA_1'], 'Index': [1, 2, 3, 4,5,6], 'SemCateOfNouns': ['', '', '', '','',''], 'GNP': ['','[m sg a]','[m sg a]','','[- - -]',''], 'DepRel': ['3:card','3:mod','4:k7','6:vmod','6:vmod','0:main'], 'Discourse': ['', '', '', '','',''], 'SpeakersView': ['', '', '', '','',''], 'Scope': ['', '', '', '','',''], 'SentenceType': ['affirmative']}, "In Edit", "3"))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['Sera_1','nIMxa_1','tUta_1-wA_hE_1'], 'Index': [1, 2, 3], 'SemCateOfNouns': ['', '', ''], 'GNP': ['[m sg a]','[f sg a]',''], 'DepRel': ['2:r6','3:k1','0:main'], 'Discourse': ['', '', ''], 'SpeakersView': ['', '', ''], 'Scope': ['', '', ''], 'SentenceType': ['affirmative']}, "In Edit", "4"))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['vaha', 'cUhA_1', 'bahuwa_1', 'gussA+kara_1-wA_hE_1'], 'Index': [1, 2, 3, 4], 'SemCateOfNouns': ['', '', '', ''], 'GNP': ['[- sg a]', '[m pl a]', '', ''], 'DepRel': ['2:nmod__adj', '4:k7', '4:nmod__adj', '0:main'], 'Discourse': ['', '', '', ''], 'SpeakersView': ['', '', '', ''], 'Scope': ['', '', '', ''], 'SentenceType': ['affirmative']}, "In Edit", "5"))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['cUhA_1','vaha','yaha','vinawI+kara_1-wA_hE_1'], 'Index': [1, 2, 3, 4], 'SemCateOfNouns': ['', '', '', ''], 'GNP': ['[m sg a]','[- sg a]','',''], 'DepRel': ['4:k1','4:k2','4:nmod__adj','0:main'], 'Discourse': ['', '', '', ''], 'SpeakersView': ['', '', '', ''], 'Scope': ['', '', '', ''], 'SentenceType': ['affirmative']}, "In Edit", "6"))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['vaha','vaha','jAna_1-yA_1','anumawi+xe_1-yA_1'], 'Index': [1, 2, 3, 4], 'SemCateOfNouns': ['', '', '', ''], 'GNP': ['[- sg a]','[- sg a]','',''], 'DepRel': ['3:k2','3:k2','4:k2','0:main'], 'Discourse': ['', '', '', ''], 'SpeakersView': ['', '', '', ''], 'Scope': ['', '', '', ''], 'SentenceType': ['affirmative']}, "In Edit", "7"))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['eka_1','xina_1','vaha','vaha','sahAyawA+kara_1-gA_1'], 'Index': [1, 2, 3, 4,5], 'SemCateOfNouns': ['', 'per', '', '',''], 'GNP': ['','[m sg a]','[- sg a]','[- sg a]',''], 'DepRel': ['2:card','5:k7t','5:k2','5:k2','0:main'], 'Discourse': ['', '', '', '',''], 'SpeakersView': ['', '', '', '',''], 'Scope': ['', '', '', '',''], 'SentenceType': ['affirmative']}, "In Edit", "8"))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['cUhA_1','bAwa_1','suna_1','Sera_1','haMsa_1-wA_hE_1'], 'Index': [1, 2, 3, 4,5], 'SemCateOfNouns': ['','','per','',''], 'GNP': ['[m pl a]','[f sg a]','','[m sg a]',''], 'DepRel': ['2:r6','3:k2','5:vmod','5:k1','0:main'], 'Discourse': ['', '', '', '',''], 'SpeakersView': ['', '', '', '',''], 'Scope': ['', '', '', '',''], 'SentenceType': ['affirmative']}, "In Edit", "9"))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id,  {'Concept': ['kuCa_1','mahInA_1','bAxa_1','eka_1','xina_1','jaMgala_1','SikArI_1','A_1-pres'], 'Index': [1, 2, 3, 4,5,6,7,8], 'SemCateOfNouns': ['','','','','per','','',''], 'GNP': ['','[m pl a]','','','[m sg a]','[m sg a]','[m sg a]',''], 'DepRel': ['2:nmod__adj','8:k7t','2:lwg__psp','5:card','8:k7t','8:k7p','8:k1','0:main'], 'Discourse': ['', '', '', '','','','',''], 'SpeakersView': ['', '', '', '','','','',''], 'Scope': ['', '', '', '','','','',''], 'SentenceType': ['affirmative']}, "In Edit", "10"))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['vaha','Sera_1','pakadZa_1-pres'], 'Index': [1, 2, 3], 'SemCateOfNouns': ['','',''], 'GNP': ['[- sg a]','[m sg a]',''], 'DepRel': ['2:nmod__adj','3:k2','0:main'], 'Discourse': ['', '', ''], 'SpeakersView': ['', '', ''], 'Scope': ['', '', ''], 'SentenceType': ['affirmative']}, "In Edit", "11"))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['vaha','rassI_1','bAMXa_1-pres'], 'Index': [1, 2, 3], 'SemCateOfNouns': ['','',''], 'GNP': ['[- sg a]','[f sg a]',''], 'DepRel': ['3:k2','3:k3','0:main'], 'Discourse': ['', '', ''], 'SpeakersView': ['', '', ''], 'Scope': ['', '', ''], 'SentenceType': ['affirmative']}, "In Edit", "12"))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['Sera_1','Kuxa','CudZA_1-yA_1','pUrA_1','koSiSa+kara_1-wA_hE_1'], 'Index': [1, 2, 3,4,5], 'SemCateOfNouns': ['','','','',''], 'GNP': ['[m sg a]','','','',''], 'DepRel': ['5:k1','3:k2','5:k2','5:mod','0:main'], 'Discourse': ['', '', '','',''], 'SpeakersView': ['', '', '','',''], 'Scope': ['', '', '','',''], 'SentenceType': ['affirmative']}, "In Edit", "13"))
            mysql.connection.commit()
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, sent_id) VALUES(%s,%s,%s,%s,%s)", (auth_id, dis_id, {'Concept': ['vaha','pareSAna+ho_1','jZora_1','xahAdZa_1-wA_hE_1'], 'Index': [1, 2, 3,4], 'SemCateOfNouns': ['','','',''], 'GNP': ['[- sg a]','','',''], 'DepRel': ['4:k1','4:vmod','4:adv','0:main'], 'Discourse': ['', '', '',''], 'SpeakersView': ['', '', '',''], 'Scope': ['', '', '',''], 'SentenceType': ['affirmative']}, "In Edit", "14"))
            mysql.connection.commit()
        return jsonify("generated Successfully")

@app.route('/getUSRid')
def getusrid():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        'SELECT USR_ID FROM usr WHERE discourse_id = % s ', (dis_id, ))
    usr_id = cursor.fetchall()
    respone = jsonify(usr_id)
    respone.status_code = 200
    return respone


@app.route('/editusr/', methods=['GET', 'POST'])
@cross_origin()
def editusr():
    if request.method == "POST":
        # email = session.get('email')
        # print(email)
        author_id = auth_id
        discourse_id = dis_id
        data = request.get_json()
        finalJson = data.get('finalJson')
        usrid = data.get('usrid')
        print("Editusr usrid:", usrid)
        # edit_usr = request.get_json()
        # sentence_id = request.get_json()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, usr_id) VALUES(%s,%s,%s,%s,%s)",
                       (auth_id, dis_id, finalJson, "In Edit", usrid))
        mysql.connection.commit()
        # print(email, author_id, discourse_id)
        dat = {'message': 'Edited Successfully!!!'}
    return jsonify(dat)
    # return jsonify(message='Edited Successfully!')


@app.route('/editstatus/', methods=['GET', 'POST'])
def editstatus():
    if request.method == "POST":
        author_id = auth_id
        discourse_id = dis_id
        data = request.get_json()
        status = data.get('status')
        usrid = data.get('usrid')
        print(status)
        print(usrid)
        # sentence_id = data.get('sentence_id')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "UPDATE edit SET status=%s WHERE usr_id=%s and discourse_id=%s", (status, usrid, dis_id))
        mysql.connection.commit()
        # print(email, author_id, discourse_id)
        dat = {'message': 'Status updated successfully'}
    return jsonify(dat)


@app.route('/get_edit_usr', methods=['GET'])
def get_edit_usr():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "SELECT edit_id, author_id, discourse_id, edited_USR, status, sent_id, edit_date FROM edit")
        usrRows = cursor.fetchall()
        respone = jsonify(usrRows)
        respone.status_code = 200
        return respone
    except Exception as e:
        print(e)


@app.route('/api/orignal_usr_fetch/')
def orignal_usr_fetch():
    global dis_id
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # print("Hello ",dis_id)
    query = 'SELECT e1.usr_id, e1.edited_usr, e1.edit_date,e1.status FROM edit e1 INNER JOIN ( SELECT usr_id, MAX(edit_date) AS max_edit_date FROM edit WHERE discourse_id =%s GROUP BY usr_id ) e2 ON e1.usr_id = e2.usr_id AND e1.edit_date = e2.max_edit_date WHERE e1.discourse_id = %s ORDER BY e1.usr_id'
    params = (dis_id, dis_id)
    print("Executing query:", query % params)
    cursor.execute(query, params)
    author_name = cursor.fetchall()
    respone = jsonify(author_name)
    respone.status_code = 200
    return respone


@app.route('/sentence_id_fetch')
def sentence_id_fetch():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        'SELECT sent_id FROM edit WHERE discourse_id = % s ', (dis_id, ))
    sent_id = cursor.fetchall()
    respone = jsonify(sent_id)
    respone.status_code = 200
    return respone


@app.route('/dashboard', methods=['GET'])
def dashboard():
    if request.method == 'GET':
        # email = session.get('email')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # cursor.execute("SELECT author_id FROM author WHERE email = %s", [email])
        # author_id = (cursor.fetchone())['author_id']
        author_id = auth_id

        cursor.execute(
            "SELECT discourse_id from discourse WHERE author_id = % s", [author_id])
        discourse_id = cursor.fetchall()

        mysql.connection.commit()
        for i in discourse_id:
            cursor.execute(
                "SELECT sentences FROM discourse WHERE discourse_id = % s", [i])
            sentences = cursor.fetchall()
            mysql.connection.commit()
            cursor.execute(
                "SELECT orignal_USR_json FROM usr WHERE discourse_id = % s", [i])
            usr = cursor.fetchall()
            mysql.connection.commit()
            usr_list = [{'discourse': sentences, 'usr': usr}]

        len_sent = len(sentences)
        len_usr = len(usr)

        return jsonify(message='Dashboard Generated!')


@ app.route('/authors')
def author():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "SELECT author_id, author_name, email, password, reviewer_role FROM author")
        authRows = cursor.fetchall()
        respone = jsonify(authRows)
        respone.status_code = 200
        return respone
    except Exception as e:
        print(e)


@ app.route('/author/<author_id>')
def auth_details(author_id):
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "SELECT author_id , author_name, email, password, reviewer_role FROM author WHERE author_id =%s", author_id)
        authRow = cursor.fetchone()
        respone = jsonify(authRow)
        respone.status_code = 200
        return respone
    except Exception as e:
        print(e)


@ app.route('/usr/<discourse_name>')
def usrin_details(discourse_name):
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        row_id = cursor.lastrowid
        print(row_id)
        cursor.execute("SELECT discourse_id FROM discourse WHERE discourse_name = %s", [
                       discourse_name])
        dis_row = cursor.fetchone()
        d_id = dis_row.get("discourse_id")
        cursor.execute(
            "SELECT author_id, discourse_id, sentence_id, orignal_USR_json FROM usr  WHERE discourse_id  =%s", [d_id])
        authRow = cursor.fetchall()
        respone = jsonify(authRow)
        respone.status_code = 200
        return respone
    except Exception as e:
        print(e)


@ app.route('/discourse')
def discourse():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "SELECT discourse_id, author_id, no_sentences, domain,create_date, other_attributes, sentences, discourse_name FROM discourse")
        disRows = cursor.fetchall()
        respone = jsonify(disRows)
        respone.status_code = 200
        return respone
    except Exception as e:
        print(e)


@ app.route('/USR')
def USR():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM usr")
        usrRows = cursor.fetchall()
        respone = jsonify(usrRows)
        respone.status_code = 200
        return respone
    except Exception as e:
        print(e)


@ app.route('/USR/<USR_ID>')
def usr_details(USR_ID):
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "SELECT author_id, discourse_id, sentence_id, USR_ID, orignal_USR_json, final_USR, create_date, USR_status FROM usr WHERE discourse_id =%s", [USR_ID])
        usrRow = cursor.fetchall()
        respone = jsonify(usrRow)
        respone.status_code = 200
        return respone
    except Exception as e:
        print(e)


@ app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str("Invalid URL")), 404


def displayUSR(corpus_for_usr):
    # Pre-processing of the corpus for USR generation.
    str1 = corpus_for_usr
    if corpus_for_usr is None:
        return jsonify("Not a Valid Sentence")

    f = open(
        "/home/var31/parser/sentences_for_USR", "w")
    # f = open(
    #     "/mnt/c/Users/gupta/OneDrive/Desktop/USR_GENERATOR/parser/sentences_for_USR", "w")
    str_end = ["।", "|", "?", "."]
    str2 = ""
    sent_id = 0
    for word in str1:

        str2 += word
        if word in str_end:
            str2 = str2.strip()
            f.write(str(sent_id)+"  "+str2+"\n")
            sent_id += 1
            str2 = ""
    f.close()
    # Clean up bulk USRs directory
    # for file in os.listdir("/mnt/c/Users/gupta/OneDrive/Desktop/USR_GENERATOR/parser/bulk_USRs"):
    #     os.remove(
    #         "/mnt/c/Users/gupta/OneDrive/Desktop/USR_GENERATOR/parser/bulk_USRs/"+file)
    # with open("/mnt/c/Users/gupta/OneDrive/Desktop/USR_GENERATOR/parser/sentences_for_USR", "r") as f:
    for file in os.listdir("/home/var31/parser/bulk_USRs"):
        os.remove(
            "/home/var31/parser/bulk_USRs/"+file)
    with open("/home/var31/parser/sentences_for_USR", "r") as f:
        for data in f:
            file_to_paste = open("/home/var31/parser/txt_files/bh-1", "w")
            # "/mnt/c/Users/gupta/OneDrive/Desktop/USR_GENERATOR/parser/txt_files/bh-1", "w")

            file_to_paste_temp = open("/home/var31/parser/bh-2", "w")

            sent = data.split("  ")[1]
            s_id = data.split("  ")[0]
            file_to_paste.write(sent)
            file_to_paste_temp.write(sent)
            file_to_paste_temp.close()
            file_to_paste.close()
            # os.system("cd /home/var31/parser")
            # os.system("ls")
            os.system(
                "python3 /home/var31/parser/sentence_check.py")
            os.system(
                "sh /home/var31/parser/makenewusr.sh /home/var31/parser/txt_files/bh-1")
            os.system(
                "python3 /home/var31/parser/generate_usr.py>/home/var31/parser/bulk_USRs/"+s_id)
            os.system(
                "python3 /home/var31/parser/delete_1.py")

    gs = []
    for file in os.listdir("/home/var31/parser/bulk_USRs"):
        usr_file = open("/home/var31/parser/bulk_USRs/"+file, "r")
        usr_list = usr_file.readlines()
        print(usr_list)
        usr_dict = {}
        usr_dict['Concept'] = usr_list[2].strip().split(",")
        usr_dict['Index'] = [int(x) for x in usr_list[3].split(",")]
        usr_dict['SemCateOfNouns'] = usr_list[4].strip().split(",")
        usr_dict['GNP'] = usr_list[5].strip().split(",")
        usr_dict['DepRel'] = usr_list[6].strip().split(",")
        usr_dict['Discourse'] = usr_list[7].strip().split(",")
        usr_dict['SpeakersView'] = usr_list[8].strip().split(",")
        usr_dict['Scope'] = usr_list[9].strip().split(",")
        usr_dict['SentenceType'] = usr_list[10].strip().split(",")
        gs.append(usr_dict)
    return jsonify(gs)
    # return "एक समय की बात है।"


@ app.route('/logout')
def logout():
    session["email"] = None
    return redirect("http://localhost:3000/")


@ app.route('/about')
def about():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    author_id = session.get('author_id')
    author_id = 1
    cursor.execute(
        'SELECT * from discourse WHERE author_id = % s ', (author_id, ))
    discourse = cursor.fetchall()
    dis = len(discourse)
    cursor.execute('SELECT * from usr')
    usr = cursor.fetchall()
    us = len(usr)
    cursor.execute(
        'SELECT distinct discourse_id from edit WHERE author_id = %s AND status= %s', (author_id, "Approved"))
    st = len(cursor.fetchall())
    response = jsonify(discourse_count=dis, usr_count=us, app_count=st)
    response.status_code = 200
    return response


@ app.route('/authName')
def authName():
    if 'author_id' not in session:
        return jsonify({'error': 'Author ID not found in session'}), 400

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        'SELECT author_name FROM author WHERE author_id = %s', (session['author_id'],))
    author_name = cursor.fetchone()

    if author_name:
        return jsonify(author_name), 200
    else:
        return jsonify({'error': 'Author name not found'}), 404



@ app.route('/api/dashboard_data')
def dashboard_data():
    try:
        if "author_id" in session :
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
                "SELECT * FROM discourse JOIN usr ON discourse.discourse_id=usr.discourse_id WHERE discourse.author_id = {0}".format(session["author_id"]))
            disRows = cursor.fetchall()
            respone = jsonify(disRows)
            respone.status_code = 200
            return respone,200
        else:
            return 400
    except Exception as e:
        print(e)


@app.route('/api/uniqu_dis', methods=['GET', 'POST'])
def uniqu_dis():
    ai=""
    if "author_id" in session:
        ai=session["author_id"]
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "SELECT distinct discourse.discourse_id,discourse_name,sentences,USR_status FROM discourse JOIN usr ON discourse.discourse_id=usr.discourse_id WHERE discourse.author_id = %s", (str(ai)))
        dasdata = cursor.fetchall()
        # print(dasdata)
        return jsonify(dasdata),200
    else :
        return "No",400
    
@app.route('/api/uniq_auth_id2', methods=['GET', 'POST'])
def uniq_auth_id2():
    ai=""
    if "author_id" in session:
        ai=session["author_id"]
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "SELECT * FROM author WHERE author_id = %s", (str(ai)))
        authdet = cursor.fetchall()
        cursor.execute(
            "SELECT * FROM discourse JOIN usr ON discourse.discourse_id=usr.discourse_id WHERE discourse.author_id = %s", (str(ai)))
        dasdata = cursor.fetchall()
        # respone = jsonify(authdet)
        return jsonify(authdet[0]),200
    else :
        return "No",400
    

@ app.route('/api/card_data')
def card_data():
    if "author_id" in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        author_id = session['author_id']
        author_id = 1
        cursor.execute(
            'SELECT * from discourse WHERE author_id = % s ', (author_id, ))
        discourse = cursor.fetchall()
        dis = len(discourse)
        cursor.execute('SELECT * from usr')
        usr = cursor.fetchall()
        us = len(usr)
        cursor.execute(
            'SELECT distinct discourse_id from edit WHERE author_id = %s AND status= %s', (author_id, "Approved"))
        st = len(cursor.fetchall())
        response = jsonify(discourse_count=dis, usr_count=us, app_count=st)
        response.status_code = 200
        return response
    else:
        return 400


@app.route('/api/fileinsert/', methods=['GET', 'POST'])
def fileinsert():
    global dis_id
    if request.method == "POST":
        data = request.get_json()
        sentences = data.get('sentences')
        discourse_name = data.get('discourse_name')
        jsondata = data.get('jsondata')
        sentencearray = data.get('sentencearray')
        no_sentences = len(sentencearray)

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT author_name FROM author WHERE author_id = % s ', (auth_id, ))
        author_id = cursor.fetchone()

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("INSERT INTO discourse(author_id, sentences, discourse_name, no_sentences) VALUES(%s, %s, %s,%s)",
                       (auth_id, sentences, discourse_name, no_sentences))
        mysql.connection.commit()
        row_id = cursor.lastrowid
        dis_id = row_id

        for i in range(no_sentences):
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
                "INSERT INTO usr(author_id, discourse_id, orignal_USR_json, USR_status) VALUES(%s, %s, %s, %s)", (auth_id, dis_id, jsondata[i], "In Edit"))
            mysql.connection.commit()
            usrid = cursor.lastrowid
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("INSERT INTO edit(author_id, discourse_id, edited_USR, status, USR_ID, sent_id) VALUES(%s, %s, %s, %s, %s, %s)",
                           (auth_id, dis_id, jsondata[i], "In Edit", usrid, '2'))
            mysql.connection.commit()

    return redirect(url_for('orignal_usr_fetch'))


def disc_id():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "SELECT discourse_id FROM discourse ORDER BY discourse_id DESC LIMIT 1;")
    dis_id = cursor.fetchall()
    a = dis_id[0]
    dis_id = a["discourse_id"]
    mysql.connection.commit()
    return dis_id


@ app.route('/read_n_enter', methods=['GET', 'POST'])
def read_n_enter():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    file = open("read/Suryast.txt", encoding="utf=8")

    read = file.read()
    file.seek(0)

    line = 1
    for word in read:
        if word == '\n':
            line += 1

    arr = []
    for i in range(line):
        arr.append(file.readline())

    sl = ""
    dis_str = ""
    l = []
    c = 1
    for x in arr:
        if "#" in x:
            dis_str += x[1:]
            c = 1
            l.append(sl)
            sl = ""

        if c <= 10:
            sl += x
            c += 1

    l.append(sl)

    # cursor.execute("INSERT INTO discourse(author_id, sentences, discourse_name) VALUES(%s, %s, %s)",
    #                (1, dis_str, "try"))

    it = 1
    for i in range(1, len(l)):
        file = open("read/out_gen/"+str(it), "w", encoding="utf=8")
        it += 1
        file.write(l[i])

    # for i in range(1, len(l)):
        cursor.execute(
            "INSERT INTO usr(author_id, discourse_id, orignal_USR_json, USR_status) VALUES(%s, %s, %s, %s)", (1, disc_id(), l[i], "In Edit"))
    mysql.connection.commit()
    return jsonify("Read and Entered")


@app.route('/view_btn_data')
def orignal_usr_fetch2():
    dis_id = request.args.get('dis_id')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        'SELECT * FROM discourse JOIN edit ON discourse.discourse_id=edit.discourse_id WHERE edit.discourse_id={0}'.format(dis_id))
    view_data = cursor.fetchall()
    response = jsonify(view_data)
    response.status_code = 200
    mysql.connection.commit()
    return response


@app.route('/view_btn_data')
def view_btn_data():
    dis_id = request.args.get('dis_id')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM discourse JOIN edit ON discourse.discourse_id=edit.discourse_id WHERE edit.discourse_id={0}'.format(dis_id))
    view_data = cursor.fetchall()
    response = jsonify(view_data)
    response.status_code = 200
    mysql.connection.commit()
    return response


@app.route('/delete_discourse')
def delete_discourse():
    dis_id = request.args.get('dis_id')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute(
        'DELETE FROM edit WHERE edit.discourse_id={0}'.format(dis_id))
    cursor.execute(
        'DELETE FROM usr WHERE usr.discourse_id={0}'.format(dis_id))
    cursor.execute(
        'DELETE FROM discourse WHERE discourse.discourse_id={0}'.format(dis_id))
    mysql.connection.commit()
    return redirect("http://localhost:3000/dashboard")


@app.route('/update_status')
def update_status():
    dis_id = request.args.get('dis_id')
    s_value = request.args.get('s_value')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute(
        'UPDATE usr SET USR_status={0} WHERE discourse_id={1}'.format(s_value, dis_id))
    cursor.execute(
        'UPDATE edit SET status={0} WHERE discourse_id={1}'.format(s_value, dis_id))

    mysql.connection.commit()
    return redirect("http://localhost:3000/dashboard")


@app.route('/semcateofnouns/', methods=['GET'])
def get_nouns():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM semcateofnouns;")
    result = cursor.fetchall()
    return jsonify([dict(row) for row in result])

@app.route('/dbsentencetype/', methods=['GET'])
def get_sentencetype():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM sentencetype;")
    result = cursor.fetchall()
    return jsonify([dict(row) for row in result])

@app.route('/dbspeakersview/', methods=['GET'])
def get_speakersview():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM speakersview;")
    result = cursor.fetchall()
    return jsonify([dict(row) for row in result])

@app.route('/dbdeprelation/', methods=['GET'])
def get_deprelation():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM deprelation;")
    result = cursor.fetchall()
    return jsonify([dict(row) for row in result])