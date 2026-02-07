from flask import Blueprint, jsonify, request, session
from flask_cors import cross_origin

from extensions import db
from models import MenuItem
from auth import require_admin, get_current_language

menu_api = Blueprint("menu_api", __name__)


def _bad_request(message: str, status_code: int = 400):
    return jsonify({"ok": False, "error": message}), status_code


@menu_api.get("/menu")
@cross_origin()
def list_menu_items():
    try:
        language = get_current_language()
        menu_items = MenuItem.query.order_by(MenuItem.id.desc()).all()
        return jsonify({
            "ok": True,
            "items": [item.to_dict(language) for item in menu_items]
        })
    except Exception as e:
        print(f"Error in list_menu_items: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@menu_api.get("/menu/available")
@cross_origin()
def list_available_menu_items():
    try:
        language = get_current_language()
        menu_items = MenuItem.query.filter_by(is_available=True).order_by(MenuItem.id.desc()).all()
        return jsonify({
            "ok": True,
            "items": [item.to_dict(language) for item in menu_items]
        })
    except Exception as e:
        print(f"Error in list_available_menu_items: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@menu_api.get("/menu/<int:item_id>")
@cross_origin()
def get_menu_item(item_id: int):
    language = get_current_language()
    menu_item = MenuItem.query.get(item_id)
    if not menu_item:
        return _bad_request("Menu item not found", 404)
    return jsonify({"ok": True, "item": menu_item.to_dict(language)})


@menu_api.post("/menu")
@cross_origin()
@require_admin
def create_menu_item():
    data = request.get_json(silent=True) or {}

    required = ["name_ar", "name_en", "description_ar", "description_en", "price"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        return _bad_request(f"Missing fields: {', '.join(missing)}")

    try:
        price = float(data["price"])
    except (TypeError, ValueError):
        return _bad_request("Invalid price")

    menu_item = MenuItem(
        name_ar=str(data["name_ar"]).strip(),
        name_en=str(data["name_en"]).strip(),
        description_ar=str(data["description_ar"]).strip(),
        description_en=str(data["description_en"]).strip(),
        price=price,
        is_available=bool(data.get("is_available", True)),
        category=str(data.get("category", "main")).strip()
    )
    
    # Handle image URLs
    image_urls = data.get("image_urls", [])
    if image_urls:
        menu_item.set_image_urls(image_urls)
    
    db.session.add(menu_item)
    db.session.commit()
    
    return jsonify({"ok": True, "item": menu_item.to_dict()}), 201


@menu_api.put("/menu/<int:item_id>")
@cross_origin()
@require_admin
def update_menu_item(item_id: int):
    menu_item = MenuItem.query.get(item_id)
    if not menu_item:
        return _bad_request("Menu item not found", 404)

    data = request.get_json(silent=True) or {}
    
    if "name_ar" in data:
        menu_item.name_ar = str(data["name_ar"]).strip()
    if "name_en" in data:
        menu_item.name_en = str(data["name_en"]).strip()
    if "description_ar" in data:
        menu_item.description_ar = str(data["description_ar"]).strip()
    if "description_en" in data:
        menu_item.description_en = str(data["description_en"]).strip()
    if "price" in data:
        try:
            menu_item.price = float(data["price"])
        except (TypeError, ValueError):
            return _bad_request("Invalid price")
    if "is_available" in data:
        menu_item.is_available = bool(data["is_available"])
    if "category" in data:
        menu_item.category = str(data["category"]).strip()
    if "image_urls" in data:
        menu_item.set_image_urls(data["image_urls"])

    db.session.commit()
    return jsonify({"ok": True, "item": menu_item.to_dict()})


@menu_api.delete("/menu/<int:item_id>")
@cross_origin()
@require_admin
def delete_menu_item(item_id: int):
    menu_item = MenuItem.query.get(item_id)
    if not menu_item:
        return _bad_request("Menu item not found", 404)
    
    db.session.delete(menu_item)
    db.session.commit()
    
    return jsonify({"ok": True})


@menu_api.put("/menu/<int:item_id>/toggle-availability")
@cross_origin()
@require_admin
def toggle_availability(item_id: int):
    menu_item = MenuItem.query.get(item_id)
    if not menu_item:
        return _bad_request("Menu item not found", 404)
    
    menu_item.is_available = not menu_item.is_available
    db.session.commit()
    
    return jsonify({
        "ok": True, 
        "item": menu_item.to_dict(),
        "message": f"Item is now {'available' if menu_item.is_available else 'unavailable'}"
    })


@menu_api.post("/menu/<int:item_id>/images")
@cross_origin()
@require_admin
def add_menu_image(item_id: int):
    menu_item = MenuItem.query.get(item_id)
    if not menu_item:
        return _bad_request("Menu item not found", 404)
    
    data = request.get_json(silent=True) or {}
    image_url = data.get("image_url", "").strip()
    
    if not image_url:
        return _bad_request("Image URL required")
    
    current_images = menu_item.get_image_urls()
    current_images.append(image_url)
    menu_item.set_image_urls(current_images)
    
    db.session.commit()
    
    return jsonify({
        "ok": True,
        "item": menu_item.to_dict(),
        "message": "Image added successfully"
    })


@menu_api.delete("/menu/<int:item_id>/images")
@cross_origin()
@require_admin
def remove_menu_image(item_id: int):
    menu_item = MenuItem.query.get(item_id)
    if not menu_item:
        return _bad_request("Menu item not found", 404)
    
    data = request.get_json(silent=True) or {}
    image_url = data.get("image_url", "").strip()
    
    if not image_url:
        return _bad_request("Image URL required")
    
    current_images = menu_item.get_image_urls()
    if image_url in current_images:
        current_images.remove(image_url)
        menu_item.set_image_urls(current_images)
        db.session.commit()
        
        return jsonify({
            "ok": True,
            "item": menu_item.to_dict(),
            "message": "Image removed successfully"
        })
    else:
        return _bad_request("Image not found", 404)
