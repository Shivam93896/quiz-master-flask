from flask import Flask,render_template, request,redirect, url_for,session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
matplotlib.use('Agg')
import os 
from werkzeug.security import generate_password_hash, check_password_hash


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'app123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quizdata.db'
    app.config['CHART_FOLDER'] = os.path.join('static','charts')
    os.makedirs(app.config['CHART_FOLDER'], exist_ok=True)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['PASSWORD_HASH'] = 'app123'
    db.init_app(app)
    return app 


db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(120),nullable = False)
    fullname = db.Column(db.String(120),nullable = False)
    username = db.Column(db.String(80), unique = True, nullable=False)
    dob = db.Column(db.Date,nullable = False)
    is_active = db.Column(db.Boolean, default = True)
    qualification = db.Column(db.String(120),nullable = False)
    
    scores = db.relationship('Score', back_populates = 'user')

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(120), nullable = False)
    
    chapters = db.relationship('Chapter', back_populates = 'subject', cascade='all, delete')


class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable = False)
    description = db.Column(db.String(120), nullable = False)
    chapter_name = db.Column(db.String(80), nullable=False)
    
    subject = db.relationship('Subject', back_populates = 'chapters')
    quiz = db.relationship('Quiz', back_populates = 'chapter', cascade='all,delete')



class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_title = db.Column(db.String(80), nullable=False)
    question_statement = db.Column(db.String(80), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable = False)
    option1 = db.Column(db.String(80), nullable=False)
    option2 = db.Column(db.String(80), nullable=False)
    option3 = db.Column(db.String(80), nullable=False)
    option4 = db.Column(db.String(80), nullable=False)
    correct_option = db.Column(db.String(80), nullable=False)
   
    quizes = db.relationship('Quiz', back_populates = 'questions')


class Quiz(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    date_of_quiz = db.Column(db.Date, nullable = False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    remarks = db.Column(db.String(80), nullable = False)
    time_of_quiz = db.Column(db.Time, nullable = False)
   
    questions = db.relationship('Question', back_populates = 'quizes', cascade='all, delete')
    scores = db.relationship('Score', back_populates = 'quizees', cascade='all, delete')
    chapter = db.relationship('Chapter', back_populates = 'quiz')



class Score(db.Model):
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    id = db.Column(db.Integer,primary_key = True)
    time_taken = db.Column(db.Time, nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    complete = db.Column(db.Integer, nullable = False)
    total_score = db.Column(db.Integer, nullable = False)
   
    user = db.relationship('User', back_populates = 'scores')
    quizees = db.relationship('Quiz', back_populates = 'scores')

def create_admin():
    admin = User.query.filter_by(username = 'admin').first()
    if not admin:
        admin = User(username = 'admin',password=generate_password_hash('admin1234'),fullname='admin12',qualification='BA',dob=datetime.strptime('2000-01-01','%Y-%m-%d'),is_active=True)
        db.session.add(admin)
        db.session.commit()

app = create_app()
app.app_context().push()
with app.app_context():
    db.create_all()
    create_admin()    
    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login',methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(username,password)
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password,password):
            if user.username == 'admin':
                session['username'] = 'admin'
                return redirect(url_for('admin_dashboard'))
            session['username'] = username 
            session['user_id'] = user.id 
            return redirect(url_for('user_dashboard'))
        else:
            return render_template('login.html', error = 'Invalid username or password')
    return render_template('login.html')    

@app.route('/admin_dashboard',methods = ['GET', 'POST'])
def admin_dashboard():
    if session.get('username') != 'admin':
        return redirect(url_for('login'))
    admin = User.query.filter_by(username='admin').first()
    admin_name = admin.fullname
    return render_template('admin_dashboard.html',admin_name=admin_name)

@app.route("/subject_manage", methods=["GET","POST"])
def subject_manage():
    subjects = Subject.query.all()
    admin_name = session.get('username')
    admin = User.query.filter_by(username='admin').first()
    admin_name = admin.fullname

    return render_template("subject_manage.html",subjects = subjects,admin_name=admin_name)

@app.route("/logout")
def logout():
    session.clear()  # Clears all session data
    return redirect(url_for("login")) 

@app.route("/search_subject", methods=["GET","POST"])
def search_subject():
    if request.method == "GET":
        query = request.args.get("subject", "").strip() 
    
        subjects = Subject.query.filter(Subject.subject_name.ilike(f"%{query}%")).all()

        return render_template("subject_manage.html", subjects=subjects, search_query=query)

@app.route("/search_quiz", methods=["GET","POST"])
def search_quiz():
    if request.method == "GET":
        query = request.args.get("quiz", "").strip() 
    
        quizes = Quiz.query.filter(Quiz.remarks.ilike(f"%{query}%")).all()

        return render_template("quiz_manage.html", quizes=quizes, search_query=query)


@app.route("/add_subject", methods=["GET","POST"])
def add_subject():
    if request.method == 'POST':
        subject_name = request.form['subject_name']
        description = request.form['description']
        subject = Subject(subject_name=subject_name,description=description)
        db.session.add(subject)
        db.session.commit()
        return redirect(url_for("subject_manage"))
    return render_template("add_subject.html")

@app.route("/edit_subject/<int:subject_id>",methods=["GET", "POST"])
def edit_subject(subject_id):
    subject = Subject.query.get(subject_id)
    if request.method == "POST":
        subject.subject_name = request.form["subject_name"]
        subject.description = request.form["description"]
        db.session.commit()
        return redirect(url_for("subject_manage"))
    return render_template("edit_subject.html", subject=subject)

@app.route("/delete_subject/<int:subject_id>", methods=["GET","POST"])
def delete_subject(subject_id):
    if request.method == "POST":
        subject = Subject.query.get(subject_id)
        db.session.delete(subject) 
        db.session.commit() 
        return redirect(url_for("subject_manage")) 
    

@app.route("/add_chapter/<int:subject_id>",methods=["GET","POST"])
def add_chapter(subject_id):
    subject = Subject.query.get(subject_id)
    if request.method == 'POST':
        chapter_name = request.form['chapter_name']
        description = request.form['description']
        chapter = Chapter(chapter_name=chapter_name,description=description,subject_id=subject_id)
        db.session.add(chapter)
        db.session.commit()
        return redirect(url_for("subject_manage"))
    return render_template("add_chapter.html", subject=subject)

@app.route("/edit_chapter/<int:chapter_id>",methods=["GET","POST"])
def edit_chapter(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if request.method == "POST":
        chapter.chapter_name = request.form["chapter_name"]
        chapter.description = request.form["description"]
        db.session.commit()
        return redirect(url_for("subject_manage"))
    return render_template("edit_chapter.html", chapter=chapter)

@app.route("/delete_chapter/<int:chapter_id>", methods=["GET","POST"])
def delete_chapter(chapter_id):
    if request.method == "POST":
        chapter = Chapter.query.get(chapter_id)
        db.session.delete(chapter)
        db.session.commit() 
        return redirect(url_for("subject_manage"))
    
    


@app.route("/quiz_manage", methods=["GET","POST"])
def quiz_manage():
    quizes = Quiz.query.all()
    chapters = Chapter.query.all()
    admin = User.query.filter_by(username='admin').first()
    admin_name = admin.fullname
    return render_template("quiz_manage.html", quizes=quizes, chapters=chapters,admin_name=admin_name)
    

@app.route("/add_quiz", methods=["GET","POST"])
def add_quiz():
    if request.method == 'POST':
        chapter_id = request.form.get('chapter_id')
        date_of_quiz = request.form.get('date_of_quiz')
        time_of_quiz = request.form.get('time_of_quiz')
        remarks = request.form.get('remarks')    
        quiz_time = datetime.strptime(time_of_quiz,'%H:%M').time()
        quiz_date = datetime.strptime(date_of_quiz,'%Y-%m-%d').date()
        quiz = Quiz(chapter_id=chapter_id, date_of_quiz=quiz_date, time_of_quiz=quiz_time,remarks=remarks)
        db.session.add(quiz)
        db.session.commit()
        return redirect(url_for("quiz_manage"))
    return render_template("add_quiz.html")

@app.route("/edit_quiz/<int:quiz_id>", methods=["GET","POST"])
def edit_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if request.method == 'POST':
        quiz.chapter_id = request.form.get("chapter_id")
        quiz.date_of_quiz = datetime.strptime(request.form.get("date_of_quiz"), "%Y-%m-%d").date()
        
        time_of_quiz = request.form.get("time_of_quiz")
        try:
            quiz.time_of_quiz = datetime.strptime(time_of_quiz, "%H:%M").time()  # Try HH:MM
        except ValueError:
            quiz.time_of_quiz = datetime.strptime(time_of_quiz, "%H:%M:%S").time()  # Try HH:MM:SS
       
        quiz.remarks = request.form.get("remarks")
        db.session.commit()
        return redirect(url_for("quiz_manage"))
    return render_template("edit_quiz.html", quiz=quiz)
    
@app.route("/delete_quiz/<int:quiz_id>", methods=["GET","POST"])
def delete_quiz(quiz_id):
    if request.method == "POST":
        quiz = Quiz.query.get(quiz_id)
        db.session.delete(quiz)
        db.session.commit() 
        return redirect(url_for("quiz_manage"))
    

@app.route("/add_question/<int:quiz_id>", methods=["GET", "POST"])
def add_question(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if request.method == "POST":
        question_title = request.form["question_title"]
        question_statement = request.form["question_statement"]
        option1 = request.form["option1"] 
        option2 = request.form["option2"] 
        option3 = request.form["option3"] 
        option4 = request.form["option4"] 
        correct_option = request.form["correct_option"] 
        question = Question(quiz_id=quiz_id,question_title=question_title,question_statement=question_statement,option1=option1,option2=option2,option3=option3,option4=option4,correct_option= correct_option)
        db.session.add(question)
        db.session.commit()
        return redirect(url_for("quiz_manage"))
    return render_template("add_question.html", quiz = quiz)

@app.route("/edit_question/<int:question_id>", methods=["GET", "POST"])
def edit_question(question_id):
    question = Question.query.get(question_id)
    if request.method == "POST":
        question.question_title = request.form["question_title"]
        question.question_statement = request.form["question_statement"]
        question.option1 = request.form["option1"] 
        question.option2 = request.form["option2"] 
        question.option3 = request.form["option3"] 
        question.option4 = request.form["option4"] 
        question.correct_option = request.form["correct_option"] 
        db.session.commit()
        return redirect(url_for("quiz_manage"))
    return render_template("edit_question.html", question=question)

@app.route("/delete_question/<int:question_id>", methods=["GET","POST"])
def delete_question(question_id):
    if request.method == "POST":
        question = Question.query.get(question_id)
        db.session.delete(question)
        db.session.commit() 
        return redirect(url_for("quiz_manage"))


@app.route("/admin_summary",methods=["GET","POST"])
def admin_summary():
    if session.get('username') != 'admin':
        return redirect(url_for('login'))
    Subject_attempt = db.session.query(Subject.subject_name,db.func.count(Score.user_id)).join(Quiz,Score.quiz_id==Quiz.id).join(Chapter,Quiz.chapter_id==Chapter.id).join(Subject,Chapter.subject_id==Subject.id).group_by(Subject.subject_name).all()
    sub_dict = dict(Subject_attempt)

    topscorer = db.session.query(Subject.subject_name,db.func.max(Score.total_score)).join(Quiz,Score.quiz_id==Quiz.id).join(Chapter,Quiz.chapter_id==Chapter.id).join(Subject,Chapter.subject_id==Subject.id).group_by(Subject.subject_name).all()
    topscorer_dict  = dict(topscorer)
    pie_labels = []
    pie_values = []
    for key, value in sub_dict.items():
        if value > 0:
            pie_labels.append(key)
            pie_values.append(value) 
    bar_labels = list(topscorer_dict.keys()) 
    bar_values = list(topscorer_dict.values())

    plt.figure(figsize=(8, 6))
    sns.barplot(x=bar_labels,y=bar_values) 
    plt.xlabel('Subject')
    plt.ylabel('Top Scorer')   
    plt.title('Top Scorers by Subject')      
    bar_chart_path = os.path.join(app.config['CHART_FOLDER'], 'bar_chart.png')
    plt.savefig(bar_chart_path)
    plt.close()

    bar_chart_url = url_for('static', filename='charts/bar_chart.png')

    plt.figure(figsize=(8,6))
    plt.pie(pie_values,labels=pie_labels, autopct='%1.1f%%')
    plt.axis('equal')
    plt.title('Subject-wise User Attempts')
    pie_chart_path = os.path.join(app.config['CHART_FOLDER'], 'pie_chart.png')
    plt.savefig(pie_chart_path)
    plt.close()

    pie_chart_url = url_for('static',filename='charts/pie_chart.png')

    return render_template("admin_summary.html",bar_chart_url=bar_chart_url,pie_chart_url=pie_chart_url)
        




@app.route('/user_dashboard',methods = ['GET', 'POST'])
def user_dashboard():
    if session.get('username') is None:
        return redirect(url_for('login'))
    quizes=Quiz.query.all()
    username = session.get('username')
    user = User.query.filter_by(username=username).first()
    user_name = user.fullname if user else "User"
    return render_template("user_dashboard.html", quizes=quizes,user_name=user_name)

@app.route('/signup',methods = ['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        fullname = request.form['fullname']
        qualification = request.form['qualification']
        dob = request.form['dob']
        user = User(username = username, password= generate_password_hash(password),fullname = fullname,qualification=qualification, dob=datetime.strptime(dob, '%Y-%m-%d').date())
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/start_quiz/<int:quiz_id>',methods=["GET","POST"])
def start_quiz(quiz_id):
    if session.get('username') is None:
        return redirect(url_for('login'))
    quiz = Quiz.query.get(quiz_id)
    questions=Question.query.filter_by(quiz_id=quiz_id).all()
    time=quiz.time_of_quiz.hour * 3600 + quiz.time_of_quiz.minute * 60 + quiz.time_of_quiz.second
    if request.method == 'POST':
        score=0
        for question in questions:
            user_answer = request.form[f'question-{question.id}']
            print(user_answer)
            if user_answer == question.correct_option:
                score += 1
                print(score)
        scores=Score(quiz_id=quiz_id, user_id=session.get('user_id'), time_taken=datetime.now().time(), total_score=score,complete=True)
        db.session.add(scores)
        db.session.commit()
        return redirect(url_for('user_dashboard'))
    return render_template('start_quiz.html', quiz=quiz, questions=questions, time=time)                

@app.route('/scores', methods=['GET','POST'])
def scores():
    if session.get('username') is None:
        return redirect(url_for('login'))
    scores=Score.query.filter_by(user_id=session.get('user_id')).all()
    return render_template('scores.html', scores=scores)

@app.route('/user_manage',methods=['GET'])
def user_manage():
    if session.get('username') != 'admin':
        return redirect(url_for('login'))
    users = User.query.all()
    return render_template('user_manage.html',users=users)

@app.route('/block_user/<int:user_id>',methods=['GET','POST'])
def block_user(user_id):
    if session.get('username') != 'admin':
        return redirect(url_for('login'))
    user=User.query.get(user_id)
   
    user.is_active = False   
    db.session.commit()
    
    return redirect(url_for('user_manage'))

@app.route('/unblock_user/<int:user_id>', methods=['GET','POST'])
def unblock_user(user_id):
    if session.get('username') != 'admin':
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    user.is_active = True  # Unblock user
    db.session.commit()
    
    return redirect(url_for('user_manage'))
   


if __name__ == '__main__':
    app.run(debug=True)



