from flask import Flask, request, jsonify
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

@app.route("/")
def home():
    return jsonify({"message": "This is a fake RFQ Submission API"})

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
