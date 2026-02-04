# The Kitchen - Cloud Kitchen Web Application

A production-ready cloud kitchen ordering system built with Flask, featuring bilingual support (Arabic/English), cart functionality, payment processing, and admin dashboard.

## Features

### Customer Features
- 🌐 **Bilingual Support**: Arabic and English language switching
- 🍽️ **Menu Browsing**: View available dishes with descriptions and images
- 🛒 **Shopping Cart**: Add items, adjust quantities, add notes
- 👤 **User Authentication**: Registration and login system
- 💳 **Payment Processing**: Multiple payment methods (Instapay, Vodafone Cash, etc.)
- 📦 **Order Tracking**: View order status and history
- 🔄 **Re-ordering**: Quick re-order from previous orders

### Admin Features
- 📊 **Dashboard**: Real-time statistics and analytics
- 📋 **Order Management**: View, update, and manage orders
- 🍴 **Menu Management**: Add, edit, delete menu items
- 💰 **Payment Verification**: Approve/reject payment screenshots
- 👥 **Customer Management**: View customer details and order history
- ⚙️ **System Settings**: Configure delivery fees, ordering status, etc.
- 📈 **Analytics**: Revenue reports and popular items

### Technical Features
- 📱 **Mobile-First Design**: Responsive layout for all devices
- 🔐 **Secure Authentication**: Session-based login system
- 🗄️ **PostgreSQL Database**: Scalable data storage
- 🚀 **RESTful APIs**: Clean API architecture
- 🌍 **CORS Support**: Cross-origin request handling
- 📧 **Email Notifications**: Order confirmations (configurable)

## Tech Stack

### Backend
- **Python 3.8+**
- **Flask** - Web framework
- **Flask-SQLAlchemy** - ORM
- **Flask-Login** - Authentication
- **Flask-CORS** - Cross-origin requests
- **PostgreSQL** - Database

### Frontend
- **HTML5** - Markup
- **Bootstrap 5** - CSS framework
- **Vanilla JavaScript** - Interactivity
- **Font Awesome** - Icons

## Installation

### Prerequisites
- Python 3.8 or higher
- PostgreSQL database
- Git

### Setup Instructions

1. **Clone the repository**
```bash
git clone <repository-url>
cd TheKitchen
```

2. **Create virtual environment**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database**
```bash
flask init-db
```

6. **Seed sample data (optional)**
```bash
flask seed-db
```

7. **Create admin user**
```python
# Run this in Python shell
from app import create_app
from models import User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    admin = User(
        name="Admin",
        email="admin@thekitchen.com",
        password_hash=generate_password_hash("admin123"),
        is_admin=True
    )
    from extensions import db
    db.session.add(admin)
    db.session.commit()
```

8. **Run the application**
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Project Structure

```
TheKitchen/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── extensions.py         # Flask extensions
├── auth.py              # Authentication utilities
├── models.py            # Database models
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
├── routes/             # API blueprints
│   ├── auth_api.py     # Authentication endpoints
│   ├── menu_api.py     # Menu management
│   ├── cart_api.py     # Shopping cart
│   ├── orders_api.py   # Order management
│   ├── payments_api.py # Payment processing
│   └── admin_api.py    # Admin functionality
├── templates/          # HTML templates
│   ├── base.html      # Base template
│   ├── index.html     # Home page
│   ├── menu.html      # Menu page
│   ├── cart.html      # Shopping cart
│   ├── signin.html    # Login page
│   ├── signup.html    # Registration page
│   └── admin/         # Admin templates
├── static/            # Static assets
│   ├── css/          # Stylesheets
│   ├── js/           # JavaScript files
│   ├── images/       # Image assets
│   └── uploads/      # User uploads
└── README.md         # This file
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user

### Menu
- `GET /api/menu` - Get all menu items
- `GET /api/menu/available` - Get available items only
- `GET /api/menu/<id>` - Get specific item
- `POST /api/menu` - Create menu item (admin)
- `PUT /api/menu/<id>` - Update menu item (admin)
- `DELETE /api/menu/<id>` - Delete menu item (admin)

### Cart
- `GET /api/cart` - Get cart contents
- `POST /api/cart` - Add item to cart
- `PUT /api/cart/<id>` - Update cart item
- `DELETE /api/cart/<id>` - Remove item from cart
- `DELETE /api/cart` - Clear cart
- `POST /api/cart/merge` - Merge guest cart with user cart

### Orders
- `GET /api/orders` - Get user orders
- `GET /api/orders/<id>` - Get order details
- `POST /api/orders` - Create new order
- `PUT /api/orders/<id>/status` - Update order status (admin)
- `POST /api/orders/<id>/reorder` - Re-order previous order

### Payments
- `GET /api/payments/methods` - Get payment methods
- `POST /api/payments` - Create payment record
- `POST /api/payments/<id>/upload` - Upload payment proof
- `PUT /api/payments/<id>/confirm` - Confirm payment (admin)
- `PUT /api/payments/<id>/reject` - Reject payment (admin)

### Admin
- `GET /api/admin/dashboard` - Dashboard statistics
- `GET /api/admin/orders` - All orders
- `GET /api/admin/customers` - Customer list
- `GET /api/admin/settings` - System settings
- `PUT /api/admin/settings` - Update settings

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | Random string |
| `NEON_CONNECTION_STRING` | PostgreSQL connection string | Required |
| `MAIL_SERVER` | SMTP server for emails | smtp.gmail.com |
| `MAIL_PORT` | SMTP port | 587 |
| `MAIL_USERNAME` | Email username | Optional |
| `MAIL_PASSWORD` | Email password | Optional |

### Application Settings

Settings can be configured via the admin panel or environment variables:

- `ORDERING_ENABLED` - Enable/disable ordering system
- `MIN_DELIVERY_FEE` - Minimum delivery fee (EGP)
- `MAX_DELIVERY_FEE` - Maximum delivery fee (EGP)
- `ADVANCE_PAYMENT_PERCENTAGE` - Required advance payment percentage

## Payment Methods

The application supports multiple Egyptian payment methods:

1. **Instapay** - Digital wallet payments
2. **Vodafone Cash** - Mobile money transfer
3. **Orange Money** - Mobile wallet service
4. **Etisalat Wallet** - Digital payment solution
5. **Cash on Delivery** - Pay on delivery (still requires advance)

## Order Status Flow

1. **New** - Order placed, awaiting payment confirmation
2. **Confirmed** - Payment verified, order accepted
3. **Preparing** - Kitchen is preparing the food
4. **On the way** - Order out for delivery
5. **Delivered** - Order successfully delivered
6. **Cancelled** - Order cancelled (by admin or customer)

## Security Features

- Session-based authentication
- CSRF protection
- Input validation and sanitization
- SQL injection prevention via SQLAlchemy ORM
- File upload restrictions
- Admin role-based access control

## Deployment

### Production Deployment

1. **Set production environment variables**
2. **Use a production WSGI server** (Gunicorn, uWSGI)
3. **Configure reverse proxy** (Nginx, Apache)
4. **Set up SSL certificate**
5. **Configure database backups**
6. **Monitor application logs**

### Docker Deployment

```dockerfile
# Dockerfile example
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Email: contact@thekitchen.com
- Phone: 01012345678

---

**Built with ❤️ for The Kitchen**
