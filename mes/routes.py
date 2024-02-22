import json
import os
import secrets
from PIL import Image
from flask import render_template, url_for, redirect, flash, request
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import or_, and_

from mes import app, db, bcrypt
from mes.forms import RegistrationForm, LoginForm, UpdateForm
from mes.models import User, Chats, Complaint, followers, requests


@app.route("/")
def home():
    if current_user.is_authenticated:
        messages = []
        users_requesting = User.query.join(followers, (followers.c.follower_id == User.id)).filter(
            followers.c.followed_id == current_user.id).all()
        users_requesting2 = User.query.join(requests, (requests.c.follower_id == User.id)).filter(
            requests.c.followed_id == current_user.id).all()

        for user in users_requesting:
            message = Chats.query.filter(or_(and_(Chats.sender_id == user.id,
                                                  Chats.receiver_id == current_user.id),
                                             and_(Chats.sender_id == current_user.id,
                                                  Chats.receiver_id == user.id))).order_by(
                Chats.date_posted.desc()).first()
            messages.append(message)
    else:
        return redirect(url_for('login'))
    return render_template('home.html', users_requesting=users_requesting, messages=messages,
                           users_requesting2=users_requesting2)


@app.route("/search")
@login_required
def search():
    username = request.args.get('search', '')
    if (username == ""):
        user_list = User.query.all()
    else:
        user_list = User.query.filter(User.username.startswith(username)).all()
    return render_template('search.html', title='Результат поиска', user_list=user_list)


@app.route("/complaint_send/<int:user_id>", methods=['POST'])
@login_required
def complaint_send(user_id):
    reason = ''
    pre_reason = request.form.getlist('reasons')
    for i in range(len(pre_reason)):
        reason += pre_reason[i]
        if (i != len(pre_reason) - 1): reason += '/'
    submit_button = request.form.get('submit_button')
    if (reason == None) or (reason == ""):
        flash("Жалоба не отправлена - причина не указана", 'danger')
        return redirect(request.referrer)

    if submit_button == 'Отправить':
        complaint = Complaint(reason=reason, offender_id=user_id, sender_id=current_user.id)
        db.session.add(complaint)
        db.session.commit()
        flash("Жалоба успешно отправлена", 'success')
    return redirect(request.referrer)


@app.route("/complaints")
@login_required
def complaints():
    if current_user.admin == 1:
        user_list = User.query.filter_by(id=Complaint.offender_id).all()
        return render_template('complaints.html', title='Список жалоб', user_list=user_list)
    else:
        flash(f"У Вас нет доступа к этой странице", 'danger')
        return render_template('blank.html')


@app.route("/complaints/<int:user_id>", methods=['GET', 'POST'])
@login_required
def complaint_analyze(user_id):
    complaint = Complaint.query.filter_by(offender_id=user_id).first()
    full = Complaint.query.filter_by(offender_id=user_id).all()
    user = User.query.filter_by(id=complaint.offender_id).first()
    sender = User.query.filter_by(id=complaint.sender_id).first()
    image_file = url_for('static', filename='profile_pics/' + user.image_file)
    if (len(full) != 1):
        flash(f"На пользователя было отправлено несколько жалоб - {len(full)}! Все причины: {full}", 'danger')
        flash(
            f"Загружена самая ранняя жалоба, отправленная по причине '{complaint.reason}' пользователем {sender.username}",
            'danger')
    else:
        flash(f"Жалоба отправлена по причине '{complaint.reason}' пользователем {sender.username}", 'danger')
    return render_template('comp_analyze.html', title=f'Жалоба на {user.username}', user=user, sender=sender,
                           complaint=complaint, image_file=image_file)


@app.route("/complaint_delete/<int:user_id><string:user_choice>", methods=['GET', 'POST'])
@login_required
def complaint_delete(user_id, user_choice):
    user = User.query.filter_by(id=user_id).first()
    complaint = Complaint.query.filter_by(offender_id=user_id).first()
    if (user_choice == 'accept'):
        if (complaint.reason == "Неприемлемый аватар"):
            user.image_file = 'default.jpg'
            user.banned = 'Неприемлемый аватар'
            db.session.commit()
        elif (complaint.reason == "Неприемлемый статус"):
            user.status = ""
            user.banned = 'Неприемлемый статус'
            db.session.commit()
    db.session.delete(complaint)
    db.session.commit()
    return redirect(url_for('complaints'))


@app.route("/ban_accept", methods=['GET', 'POST'])
def ban_accept():
    current_user.banned = None
    db.session.commit()
    return redirect(request.referrer)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Добро пожаловать в Восток!', 'success')
        login_user(user)
        user.online = True
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('register.html', title='Регистрация', form=form)


@app.route("/register_admin", methods=['GET', 'POST'])
@login_required
def register_admin():
    if ((current_user.is_authenticated) and (current_user.admin != True)):
        return redirect(url_for('home'))
    if (current_user.is_authenticated == False):
        return redirect(url_for('register'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, password=hashed_password, admin=True)
        db.session.add(user)
        db.session.commit()
        flash('Новый администратор успешно зарегистрирован!', 'success')
        return redirect(url_for('home'))
    return render_template('register_admin.html', title='Регистрация администратора', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    else:
        current_user.is_online = False
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            user.online = True
            db.session.commit()
            next_page = request.args.get('next')
            flash('С возвращением в Восток!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Указанное имя пользователя и пароль не соответствуют ни одной учетной записи. Попробуйте еще раз.',
                  'danger')
    return render_template('login.html', title='Вход', form=form)


@app.route("/logout")
def logout():
    current_user.online = False
    db.session.commit()
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture, x, y, folder):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/' + folder, picture_fn)

    output_size = (x, y)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['POST', 'GET'])
@login_required
def account():
    form = UpdateForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data, 150, 150, 'profile_pics')
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.status = form.status.data
        db.session.commit()
        flash('Данные обновлены!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.status.data = current_user.status
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    friends = db.session.query(followers).filter_by(follower_id=current_user.id).count()
    followers2 = db.session.query(requests).filter_by(followed_id=current_user.id).count()
    return render_template('account.html', title='Моя страница', image_file=image_file, form=form,
                           user=current_user, followers=followers2,
                           friends=friends)


# Маршрут для просмотра профилей пользователей
@app.route("/user/<string:username>")
@login_required
def user_account(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user == current_user:
        return redirect(url_for('account'))
    form = UpdateForm()
    form.username.data = user.username
    image_file = url_for('static', filename='profile_pics/' + user.image_file)
    if (current_user.is_following(user) and not (user.is_following(current_user))):
        following2(user.id, current_user)
        fon = 'Добавить в друзья'
    elif (user.is_following(current_user) and not (current_user.is_following(user))):
        following2(current_user.id, user)
        fon = 'Добавить в друзья'
    elif current_user.is_following(user):
        fon = 'Удалить из друзей'
    else:
        if (user.is_requesting(current_user) and current_user.is_requesting(user)):
            accept_or_delete('accept', user.id)
            accept2(current_user.id, user)
            fon = 'Удалить из друзей'
        elif user.is_requesting(current_user):
            fon = 'Ответить на заявку'
        elif current_user.is_requesting(user):
            fon = 'Отменить заявку'
        else:
            fon = 'Добавить в друзья'
    friends = db.session.query(followers).filter_by(follower_id=user.id).count()
    followers2 = db.session.query(requests).filter_by(followed_id=user.id).count()
    return render_template('account.html', title=username,
                           image_file=image_file,
                           form=form,
                           user=user,
                           followed_or_not=fon,
                           followers=followers2,
                           friends=friends)


@app.route("/status")
@login_required
def change_status():
    if current_user.online == False:
        current_user.online = True
        db.session.commit()
    else:
        current_user.online = False
    db.session.commit()
    return redirect(request.referrer)


@app.route("/chatting/<int:user_id>", methods=['GET', 'POST'])
@login_required
def chat(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    if ((user.id == current_user.id) or (not (current_user.is_following(user)))):
        flash('Невозможно перейти в диалог с этим пользователем', 'danger')
        return redirect(url_for('home'))
    messages = Chats.query.filter(or_(and_(Chats.sender_id == user_id,
                                           Chats.receiver_id == current_user.id),
                                      and_(Chats.sender_id == current_user.id,
                                           Chats.receiver_id == user_id))).all()
    return render_template('chat.html', messages=messages,
                           user=current_user, friend=user, title=f'Чат с {user.username}')


@app.route("/chatting/message/<string:message>/<int:user_id>", methods=['POST', 'GET'])
@login_required
def send_message(message, user_id):
    if message != 'voidmessagevoidmessage':
        chat = Chats(message=message, sender_id=current_user.id, receiver_id=user_id)
        db.session.add(chat)
        db.session.commit()
    messages = Chats.query.filter(or_(and_(Chats.sender_id == user_id,
                                           Chats.receiver_id == current_user.id),
                                      and_(Chats.sender_id == current_user.id,
                                           Chats.receiver_id == user_id))).all()
    messages_data = []
    for message in messages:
        message_data = {
            'message': message.message,
            'sender': message.sender_id,
            'date': message.date_posted.strftime('%H:%M')}
        messages_data.append(message_data)
    return json.dumps(messages_data)

@app.route("/following/<int:followed_id>")
@login_required
def following(followed_id):
    user = current_user
    followed = User.query.filter_by(id=followed_id).first_or_404()
    if not user.is_following(followed):
        if not user.is_requesting(followed) and not user.is_following(followed):
            event = user.request(followed)
            db.session.add(event)
            db.session.commit()
        else:
            event = user.unrequest(followed)
            db.session.add(event)
            db.session.commit()
    else:
        event = user.unfollow(followed)
        db.session.add(event)
        db.session.commit()
    return redirect(url_for('user_account', username=followed.username))


def following2(follower_id, username):
    user = username
    follower = User.query.filter_by(id=follower_id).first_or_404()
    event = user.unfollow(follower)
    db.session.add(event)
    db.session.commit()
    return redirect(url_for('user_account', username=username))


@app.route("/friends")
@login_required
def friend_list():
    users_requesting = User.query.join(followers, (followers.c.follower_id == User.id)).filter(
        followers.c.followed_id == current_user.id).all()
    return render_template('friends.html', title='Список друзей', users_requesting=users_requesting)


@app.route("/friends/<int:user_id>")
@login_required
def user_friend_list(user_id):
    users_requesting = User.query.join(followers, (followers.c.follower_id == User.id)).filter(
        followers.c.followed_id == user_id).all()
    return render_template('friends2.html', title=f'Список друзей', users_requesting=users_requesting)


@app.route("/requests")
@login_required
def handle_request():
    users_requesting = User.query.join(requests, (requests.c.follower_id == User.id)).filter(
        requests.c.followed_id == current_user.id).all()
    return render_template('requests.html', title='Заявки в друзья', users_requesting=users_requesting)


def delete_request(follower):
    event = follower.unrequest(current_user)
    db.session.add(event)
    db.session.commit()


@app.route("/requests/<int:user_id>")
@login_required
def user_requests(user_id):
    users_requesting = User.query.join(requests, (requests.c.follower_id == User.id)).filter(
        requests.c.followed_id == user_id).all()
    return render_template('requests2.html', title='Подписчики', users_requesting=users_requesting)


@app.route("/requests/accept_or_delete/<int:follower_id><string:user_choice>", methods=['GET', 'POST'])
@login_required
def accept_or_delete(user_choice, follower_id):
    follower = User.query.filter_by(id=follower_id).first_or_404()
    print(current_user)
    if user_choice == 'accept':
        event = follower.follow(current_user)
        db.session.add(event)
        db.session.commit()
    delete_request(follower)
    return redirect(url_for('handle_request'))


@app.route("/requests/accept2/<int:follower_id><string:username>", methods=['GET', 'POST'])
@login_required
def accept2(follower_id, username):
    follower = User.query.filter_by(id=follower_id).first_or_404()
    event = follower.follow(username)
    db.session.add(event)
    db.session.commit()
    event = follower.unrequest(username)
    db.session.add(event)
    db.session.commit()
    return redirect(url_for('handle_request'))
