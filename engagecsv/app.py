import os
import pandas as pd
import clearbit
import csv
import json
from flask import Flask, render_template, request, send_file
clearbit.key = 'sk_1915de5d2d7b6e245d6613e3d2188368'

app = Flask(__name__)

APP__ROOT = os.path.dirname(os.path.abspath(__file__))


@app.route("/")
def index():
    return render_template("upload.html")

@app.route("/return-file/")
def return_file():

    return send_file('new.csv', as_attachment=True)


@app.route("/upload", methods=['POST'])
def upload():
    global new_path
    target = os.path.join(APP__ROOT)
    print(target)

    if not os.path.isdir(target):
        os.mkdir(target)

    for file in request.files.getlist("file"):
        print(file)
        filename = file.filename
        destination = "/".join([target, filename])
        print(destination)
        file.save(destination)
        new_path = os.path.abspath(filename)
        print(new_path)
    df = pd.read_csv(new_path, sep=',', encoding="utf-8")
    df = df[df['Summary 1'].notnull()]
    tmp_df = df.pop('Summary 1').str.split(' - ')
    df['Location'], df['Position'], df['Company'] = tmp_df.str[0], tmp_df.str[1:-1].str.join(sep='-'), tmp_df.str[-1]
    df[['City', 'Country']] = df['Location'].str.rsplit(', ', n=1, expand=True)
    df.fillna('', inplace=True)

    def clear_data(x):
        fname = x['First Name']
        lname = x['Last Name'].strip()
        url = x['Profile URL']
        if not lname:
            fname = fname.split(' ')[0]
            url_name = url.split('/')[-1].split('-')
            if len(url_name) > 1:
                lname = url_name[-2].title()
            else:
                index_of_fname = url_name[0].lower().find(fname.lower())
                if index_of_fname != -1:
                    index_of_fname += len(fname)
                    lname = url_name[0][index_of_fname:].title()

            x['First Name'] = fname
            x['Last Name'] = lname
        else:
            lname = lname.split('-')[0].strip()
            x['Last Name'] = lname

        return x

    df.apply(clear_data, axis=1)

    tmp1_df = df.pop('Position').str.split('-')
    df['Position'] = tmp1_df.str[0]
    tmp1_df = df.pop('Position').str.split(',')
    df['Position'] = tmp1_df.str[0]
    df = df.rename(columns=({'First Name': 'Firstname'}))
    df = df.rename(columns=({'Last Name': 'Lastname'}))
    df.drop('Summary 2', axis=1, inplace=True)

    df = df[['Firstname', 'Lastname', 'Email', 'Profile URL', 'Position', 'Company', 'City', 'Country', 'Location']]
    # print (df)
    # df = pd.concat([df, df], 1)
    def extract_ascii(x):
        string_list = filter(lambda y : ord(y) < 128, x)
        return ''.join(string_list)
    df.Position = df.Position.apply(extract_ascii)
    df.Company = df.Company.apply(extract_ascii)
    df.to_csv("new.csv",index = False)
    df = pd.read_csv("new.csv", sep=',', encoding="utf-8")
    df = df[df['Lastname'].notnull()]
    df.to_csv("new.csv", index=False)
    df = pd.read_csv("new.csv", sep=',', encoding="utf-8")
    saved_column = df['Company'].dropna()
    i = 0
    res = []
    for ddata in saved_column:
        n = saved_column.get(i)
        data = clearbit.NameToDomain.find(name=n)
        i = i + 1
        if data != None:
            res.append(data['domain'])
        else:
            res.append('domain.com')
    df['Domain'] = res
    df.to_csv("new.csv", index=False)
    df = pd.read_csv("new.csv", sep=',', encoding="utf-8")
    df = df[df['Domain'] != 'domain.com']
    df.to_csv("new.csv", index=False)
    downloadpath = "new.csv"
    os.remove(os.path.abspath(new_path) )


    return render_template("complete.html", name=downloadpath)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
