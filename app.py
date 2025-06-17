from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
# Initialize Flask app
app = Flask(__name__)

# Configure SQLite DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rfq_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ensure /tmp directory exists for Render compatibility
os.makedirs('/tmp', exist_ok=True)

db = SQLAlchemy(app)

# Define the RFQ model
class RFQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(255), nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    product_sku = db.Column(db.String(100), nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    requested_price = db.Column(db.Float, nullable=False)
    requested_quantity = db.Column(db.Integer, nullable=False)
    annual_estimated_volume = db.Column(db.Integer, nullable=False)
    factory = db.Column(db.String(255), nullable=False)
    delivery_date = db.Column(db.Date, nullable=False)
    application = db.Column(db.String(255), nullable=False)
    comments = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create the DB
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return jsonify({"message": "This is the RFQ API homepage."})


# Step 1: collect email and product_name only
@app.route('/start_rfq', methods=['POST'])
def start_rfq():
    data = request.get_json()
    user_email = data.get('user_email')
    product_name = data.get('product_name')

    if not user_email or not product_name:
        return jsonify({"error": "user_email and product_name are required."}), 400

    # Construct the UI URL
    form_url = url_for('rfq_form', user_email=user_email, product_name=product_name, _external=True)

    return jsonify({
        "message": "RFQ initialization successful.",
        "form_url": form_url
    }), 200

# Step 2: render RFQ form pre-filled with collected info
@app.route('/rfq_form')
def rfq_form():
    user_email = request.args.get('user_email', '')
    product_name = request.args.get('product_name', '')

    form_html = '''
    <html>
    <head><title>Submit RFQ</title></head>
    <body>
    <h2>Request for Quotation (RFQ)</h2>
    <form method="POST" action="/submit_rfq_form">
        <label>Email: <input type="email" name="user_email" value="{{ user_email }}" required></label><br>
        <label>Product Name: <input type="text" name="product_name" value="{{ product_name }}" required></label><br>
        <label>Company Name: <input type="text" name="company_name"></label><br>
        <label>Product SKU: <input type="text" name="product_sku"></label><br>
        <label>Requested Price: <input type="number" name="requested_price" step="0.01"></label><br>
        <label>Requested Quantity: <input type="number" name="requested_quantity" required></label><br>
        <label>Annual Estimated Volume: <input type="number" name="annual_estimated_volume"></label><br>
        <label>Factory: <input type="text" name="factory"></label><br>
        <label>Delivery Date (MM/DD/YYYY): <input type="text" name="delivery_date"></label><br>
        <label>Application: <input type="text" name="application"></label><br>
        <label>Comments:<br><textarea name="comments" rows="4" cols="40"></textarea></label><br>
        <input type="submit" value="Submit RFQ">
    </form>
    </body></html>
    '''
    return render_template_string(form_html, user_email=user_email, product_name=product_name)

# Step 3: handle full form submission
@app.route('/submit_rfq_form', methods=['POST'])
def submit_rfq_form():
    try:
        def to_int(val, default=0):
            return int(val) if val and val.strip().isdigit() else default

        def to_float(val, default=0.0):
            try:
                return float(val)
            except (ValueError, TypeError):
                return default

        def to_date(val, default_str='12/31/2099'):
            try:
                return datetime.strptime(val, '%m/%d/%Y').date()
            except (ValueError, TypeError):
                return datetime.strptime(default_str, '%m/%d/%Y').date()

        rfq = RFQ(
            user_email=request.form['user_email'],
            company_name=request.form.get('company_name', 'Unknown Company'),
            product_sku=request.form.get('product_sku', 'N/A'),
            product_name=request.form['product_name'],
            requested_price=to_float(request.form.get('requested_price')),
            requested_quantity=to_int(request.form.get('requested_quantity'), default=1),
            annual_estimated_volume=to_int(request.form.get('annual_estimated_volume')),
            factory=request.form.get('factory', 'Not Specified'),
            delivery_date=to_date(request.form.get('delivery_date')),
            application=request.form.get('application', 'General Use'),
            comments=request.form.get('comments', '')
        )

        db.session.add(rfq)
        db.session.commit()

        return '''<html><body>
        <h3>✅ RFQ submitted successfully!</h3>
        <a href="/rfq_form?user_email=&product_name=">Submit another RFQ</a>
        </body></html>'''

    except Exception as e:
        return f"<html><body><h3>Error: {str(e)}</h3></body></html>", 400




# Route to submit an RFQ
@app.route('/submit_rfq', methods=['POST'])
def submit_rfq():
    data = request.get_json()

    try:
        # Validate required fields
        if not all(k in data for k in ['user_email', 'product_name', 'requested_quantity']):
            return jsonify({"error": "Missing required fields: user_email, product_name, or requested_quantity"}), 400

        # Set default values
        rfq = RFQ(
            user_email=data['user_email'],
            company_name=data.get('company_name', 'Unknown Company'),
            product_sku=data.get('product_sku', 'N/A'),
            product_name=data['product_name'],
            requested_price=float(data.get('requested_price', 0.0)),
            requested_quantity=int(data['requested_quantity']),
            annual_estimated_volume=int(data.get('annual_estimated_volume', 0)),
            factory=data.get('factory', 'Not Specified'),
            delivery_date=datetime.strptime(data.get('delivery_date', '2099-12-31'), '%Y-%m-%d').date(),
            application=data.get('application', 'General Use'),
            comments=data.get('comments', '')
        )

        db.session.add(rfq)
        db.session.commit()
        return jsonify({"message": "RFQ submitted successfully."}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Route to get all RFQs
@app.route('/rfqs', methods=['GET'])
def get_rfqs():
    rfqs = RFQ.query.order_by(RFQ.submitted_at.desc()).all()
    return jsonify([{ 
        "id": r.id,
        "user_email": r.user_email,
        "company_name": r.company_name,
        "product_sku": r.product_sku,
        "submitted_at": r.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
    } for r in rfqs])

# Route to get RFQ detail by ID
@app.route('/rfq/<int:rfq_id>', methods=['GET'])
def get_rfq_detail(rfq_id):
    rfq = RFQ.query.get_or_404(rfq_id)
    return jsonify({
        "id": rfq.id,
        "user_email": rfq.user_email,
        "company_name": rfq.company_name,
        "product_sku": rfq.product_sku,
        "product_name": rfq.product_name,
        "requested_price": rfq.requested_price,
        "requested_quantity": rfq.requested_quantity,
        "annual_estimated_volume": rfq.annual_estimated_volume,
        "factory": rfq.factory,
        "delivery_date": rfq.delivery_date.strftime('%Y-%m-%d'),
        "application": rfq.application,
        "comments": rfq.comments,
        "submitted_at": rfq.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
    })

# Route to delete RFQ by ID
@app.route('/rfq/<int:rfq_id>', methods=['DELETE'])
def delete_rfq(rfq_id):
    rfq = RFQ.query.get_or_404(rfq_id)
    db.session.delete(rfq)
    db.session.commit()
    return jsonify({"message": f"RFQ ID {rfq_id} deleted successfully."})

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
