from mes import loginManager, db, app
from flask_login import UserMixin
from datetime import datetime

@loginManager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
                     )

requests = db.Table('requests',
                    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
                    )


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(120))
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    online = db.Column(db.Boolean, default=0)
    admin = db.Column(db.Boolean, default=0)
    banned = db.Column(db.String(40), default=None)
    followed = db.relationship('User',
                               secondary=followers,
                               primaryjoin=(followers.c.follower_id == id),
                               secondaryjoin=(followers.c.followed_id == id),
                               backref=db.backref('followers', lazy='dynamic'),
                               lazy='dynamic')
    requested_by = db.relationship('User',
                                   secondary=requests,
                                   primaryjoin=(requests.c.follower_id == id),
                                   secondaryjoin=(requests.c.followed_id == id),
                                   backref=db.backref('requests', lazy='dynamic'),
                                   lazy='dynamic')

    # Методы для работы с запросами, подписчиками и друзьями
    def request(self, user):
        if not self.is_requesting(user):
            self.requested_by.append(user)
            return self

    def is_requesting(self, user):
        return self.requested_by.filter(requests.c.followed_id == user.id).count() > 0

    def unrequest(self, user):
        if self.is_requesting(user):
            self.requested_by.remove(user)
            return self

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            return self

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            return self

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def __repr__(self):
        return 'User(%s, %s, %s )' % (self.username, self.image_file, self.id)

class Chats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(50), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return '%s, %s, %s' % (self.message, self.sender_id, self.receiver_id) #Для вывода чата


class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reason = db.Column(db.String(50), nullable=False)
    offender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    commentary = db.Column(db.String(50))

    def __repr__(self):
        return '%s' % (self.reason) #Для вывода причин при нескольких жалобах