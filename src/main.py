from flask import Flask, session, render_template, request, Response
import random, string, json, glob, os
from Bio import AlignIO, motifs, Seq
from flask_sqlalchemy import SQLAlchemy

MAX_QUERY_SIZE = 500

alignments = [AlignIO.read(f, 'gb') for f in glob.glob('proteins/*')]

app = Flask(__name__)
for config_key in ['DEBUG', 'SECRET_KEY', 'SQLALCHEMY_DATABASE_URI']:
  app.config[config_key] = os.environ.get(config_key)

db = SQLAlchemy(app)

# Represents a given query from a user (randomly generated session key). A query that
# doesn't match any protein will have NULL for `matched_protein` and `match_pos`.
class Alignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(10), unique=False, nullable=False, index=True)
    matched_protein = db.Column(db.String(20), unique=False, nullable=True)
    # Query from the user
    alignment_query = db.Column(db.String(MAX_QUERY_SIZE), unique=False, nullable=False)
    # Starting index of the match
    match_pos = db.Column(db.Integer, unique=False, nullable=True)

if app.config['DEBUG']:
    db.drop_all()
    db.create_all()

@app.route("/")
def index():
    return render_template('index.html')

# Searches proteins db to find a sequence match
# from the inputted sequence query.
@app.route("/align", methods=["POST"])
def align():
    user = get_username()
    
    # Sanitize and validate input
    query = request.form["query"].strip()
    query = ''.join(query.split())
    if not query: 
      return Response("Empty sequence query", status=412)

    if len(query) > MAX_QUERY_SIZE: 
      return Response("Query is longer than max query size of %d" % MAX_QUERY_SIZE, status=412)

    try:
        seq_motif = motifs.create([Seq.Seq(query)])
    except KeyError:
        return Response("Invalid character(s) in sequence query", status=412)
    
    # Iterate over proteins randomly
    for alignment in random.sample(alignments, len(alignments)):
        # Check for exact sequence matches, persist first match
        for pos, seq in seq_motif.instances.search(alignment[0].seq):
            matched_protein = alignment[0].name
            db.session.add(Alignment(username=user, match_pos=pos, matched_protein=matched_protein, alignment_query=query))
            db.session.commit()
            return ""

    # No match found; persist empty match.
    db.session.add(Alignment(username=user, match_pos=None, matched_protein=None, alignment_query=query))
    db.session.commit()
    return ""
   
# Get all alignment queries for this user
@app.route("/all-alignments")
def all_alignments():
    user = get_username()
    queries_for_user = Alignment.query.filter_by(username=user).all()
    return json.dumps([(row.matched_protein, row.alignment_query, row.match_pos) for row in queries_for_user])

def get_username():
    if 'username' not in session:
        session['username'] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return session['username']

if __name__ == "__main__":
    app.run()
