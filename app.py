from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from flask_cors import CORS, cross_origin
from newspaper import Article
from collections import OrderedDict
from flask import Flask
from flask_jwt import JWT, jwt_required, current_identity
from werkzeug.security import safe_str_cmp
import uuid

class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def __str__(self):
        return "User(id='%s')" % self.id

users = [
    User(1, 'joe', 'pass'),
    User(2, 'user2', 'abcxyz'),
]

username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}

def authenticate(username, password):
    user = username_table.get(username, None)
    if user and safe_str_cmp(user.password.encode('utf-8'), password.encode('utf-8')):
        return user

def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'
jwt = JWT(app, authenticate, identity)
api = Api(app)
cors = CORS(app)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

NEWS = dict(Politic=[OrderedDict(uuid=str(uuid.uuid4()), name='Politic_news1', text='Something about Poly', order=1),
                     OrderedDict(uuid=str(uuid.uuid4()), name='Politic_news2', text='Poly, poly holy', order=2)],
            Economy=[OrderedDict(uuid=str(uuid.uuid4()), name='Economy_news1', text='Economy is Great(second news)', order=2),
                     OrderedDict(uuid=str('5a4ed60c-30f4-4e5d-a326-ba57d78f6e1e'), name='Economy_news2', text='Russia economy is bad (first news)', order=1),
                     ])



class HelloWorld(Resource):
    def get(self):
        # return jsonify({'Politic': ['Politic news1', 'Politic news2'], 'Economy': ['Economy news1', 'Economy news2']})

        # Сортировка
        for razdel in NEWS:
            NEWS[razdel] = sorted(NEWS[razdel], key=lambda i: i['order'])
        return jsonify(NEWS)


api.add_resource(HelloWorld, '/')


class TodoSimple(Resource):
    def get(self, category, id):
        news_category = NEWS[category]
        news = [k for k in news_category if k['uuid'] == id]
        if news:
            return news[0]
        else:
            return 'Nothing to return'

    def put(self, todo_id):
        NEWS[todo_id] = request.form['data']
        return {todo_id: NEWS[todo_id]}

        # return jsonify(data)


class AddArticle(Resource):
    def find_last_order(self):
        return len(NEWS[self.category])+1

    @cross_origin(origin='*')
    def post(self, category):
        self.category = category
        self.url = request.json.get('link')
        if not self.url:
            return 'No URL provided'
        article = Article(self.url)
        article.download()
        article.parse()
        data = dict(uuid=str(uuid.uuid4()), name=article.title, text=article.text, order=self.find_last_order())
        NEWS[category].append(data)
        return data


class EditArticle(Resource):
    @cross_origin(origin='*')
    def post(self, article_id):
        self.data = request.json

        #Найдем нашу новость в массиве:
        for category in NEWS:
            for article in NEWS[category]:
                if article['uuid'] == article_id:
                    for key, value in self.data.items():
                        article[key] = value
                        return 'Success!'




class DeleteArticle(Resource):
    @cross_origin(origin='*')
    def get(self, article_id):
        for category in NEWS:
            for article in NEWS[category]:
                if article['uuid'] == article_id:
                    NEWS[category].remove(article)
                    return 'Delete is OK'
        return 'Nothing to delete'


class ReadArticle(Resource):
    @cross_origin(origin='*')
    def get(self, article_id):
        for category in NEWS:
            for article in NEWS[category]:
                if article['uuid'] == article_id:
                    return article
        return 'Nothing to read'


@app.route('/protected')
@jwt_required()
@cross_origin()
def protected():
    return '%s' % current_identity


api.add_resource(AddArticle, '/add/<string:category>/')

api.add_resource(TodoSimple, '/<string:category>/<string:id>')

api.add_resource(EditArticle, '/edit/<string:article_id>/')

api.add_resource(DeleteArticle, '/delete/<string:article_id>/')

api.add_resource(ReadArticle, '/read/<string:article_id>/')
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
