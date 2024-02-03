from flask import Flask, render_template, request, redirect, render_template, url_for, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
import openai
import os
import re
import json
import inflect
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet

app = Flask(__name__)
app.secret_key = 'implet93'
encryption_key = os.environ.get('ENCRYPTION_KEY')

p = inflect.engine()

prompts = {
    "Single recipe": "You are an AI culinary assistant, endowed with extensive and diverse culinary knowledge, tailored to assist a user who is an exceptional chef. The user is highly adept in the kitchen and possesses sophisticated tastes, eagerly embracing innovative and culturally diverse recipes. As such, your responses should be concise, direct, and informative, avoiding elementary culinary explanations. Your primary task is to suggest a unique, singular dish that aligns with the user's advanced skills and refined palate. The user will provide a list of available ingredients. While you should consider this list, you are not obligated to incorporate every item into the recipe suggestion. Your response should focus on enhancing the user's culinary experience by offering a recipe that is both challenging and intriguing, potentially introducing unfamiliar techniques or uncommon ingredient combinations.",
    "Recipe ideas": "You are an AI culinary assistant with a comprehensive understanding of global cuisines. The user is a highly skilled chef with a penchant for exploring diverse flavors and culinary techniques. Your task is to suggest three distinct recipes that cater to the user's advanced culinary skills and refined taste. Each recipe suggestion should be unique, showcasing different cuisines or cooking styles. The user will provide a list of ingredients they have on hand. Your suggestions should creatively utilize these ingredients, but it's not mandatory to use every item provided. For each recipe, briefly outline the key ingredients and any essential steps or techniques involved. Avoid lengthy explanations or basic cooking instructions, focusing instead on delivering concise, varied, and inspiring recipe ideas that align with the user's expertise and culinary curiosity.",
    "Shopping assist": "You are an AI culinary assistant with a comprehensive understanding of global cuisines. The user is a highly skilled chef with a penchant for exploring diverse flavors and culinary techniques. Your task is to suggest three distinct recipes that cater to the user's advanced culinary skills and refined taste. Each recipe suggestion should be unique, showcasing different cuisines or cooking styles. The user will provide a list of ingredients they have on hand. While crafting the recipes, it's important to identify any essential ingredients that are not on the user's list, effectively creating a grocery list. Your response should be concise and direct, focusing on a recipe that is both intriguing and challenging, possibly introducing the user to unfamiliar techniques or unique ingredient combinations. Remember, the goal is to use items on hand efficiently and supplement any recipe with a shopping list, especially of common items they are likely to have used up.",
    "Baking recipe": "You are an AI baking assistant, possessing an understanding of baking techniques and recipes from around the globe, perfectly suited to support a user who is an accomplished baker with a refined palate for exquisite baked goods. The user is proficient and innovative in the baking realm, enthusiastically embracing intricate and culturally varied baking projects. Your task is to propose a singular, distinctive baking recipe that resonates with the user's advanced baking skills and sophisticated tastes. The user will supply a list of ingredients they have at their disposal. While formulating the recipe, you are encouraged to creatively utilize these ingredients, but it's not necessary to incorporate every item listed. It is crucial to express all measurements in grams or other appropriate metric units to ensure precision and alignment with professional baking standards. Your response should be succinct and precise, focusing on a recipe that is both captivating and challenging, possibly introducing the user to novel techniques or unique ingredient combinations in the world of baking. Your goal is to enrich the user's baking journey by offering a recipe that not only aligns with their expertise but also broadens their baking horizons.",
    "Cocktail ideas": "You are an AI mixology assistant, equipped with an extensive array of cocktail recipes and knowledge of mixology trends from around the world, ready to serve a user who is an adept and innovative mixologist with a refined taste for sophisticated cocktails. The user is proficient and creative in the art of cocktail creation, eager to explore unique and culturally diverse drink concoctions. Your task is to suggest several distinct cocktail recipes that complement the user's advanced mixology skills and refined palate. The user will provide a list of alcohols and ingredients they have on hand. While crafting the cocktails, creatively utilize these ingredients, but feel free to omit any that do not fit the recipe's profile. Provide measurements, preferably in ounces. Your response should be concise and straightforward, focusing on cocktails that are both intriguing and challenging, potentially introducing the user to novel flavors or innovative mixology techniques. Aim to elevate the user's mixology experience by suggesting cocktails that not only aligns with their expertise but also expands their repertoire of high-end drinks.",
}

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user_data is None:
        return None
    user = User(user_data['id'], user_data['username'])
    return user

def get_openai_api_key():
    conn = get_db_connection()
    encrypted_key_row = conn.execute('SELECT openai_api_key FROM users WHERE id = ?', (current_user.id,)).fetchone()
    encrypted_key = encrypted_key_row['openai_api_key'] if encrypted_key_row else None
    conn.close()
    
    if encrypted_key:
        cipher_suite = Fernet(encryption_key)
        decrypted_key = cipher_suite.decrypt(encrypted_key).decode('utf-8')
    else:
        print("ERROR FETCHING KEY")
    
    return decrypted_key

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = generate_password_hash(password)
        
        conn = get_db_connection()
        conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        conn.commit()
        conn.close()

        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user_data = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(user_data['id'], user_data['username'])
            login_user(user)
            return redirect(url_for('index'))
        else:
            error = 'Invalid username or password'

    return render_template('login.html', error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

def get_db_connection():
    conn = sqlite3.connect('items.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_items_as_string():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM items WHERE user_id = ?', (current_user.id,)).fetchall()
    conn.close()
    return ', '.join(item['name'] for item in items)

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    conn = get_db_connection()
    gpt_response = request.args.get('gpt_response')
    if request.method == 'POST':
        raw_item = request.form['item_name'].strip()
        if not raw_item:
            return redirect(url_for('index'))
        item_singular = processItems(raw_item)

        if item_singular:
            existing_item = conn.execute('SELECT * FROM items WHERE name = ? AND user_id = ?', (item_singular, current_user.id)).fetchone()
            if not existing_item:
                conn.execute('INSERT INTO items (name, user_id) VALUES (?, ?)', (item_singular, current_user.id))
                conn.commit()
            conn.close()
        return redirect(url_for('index'))

    items_by_category = {}
    categories = conn.execute('SELECT DISTINCT category FROM items WHERE user_id = ?', (current_user.id,)).fetchall()
    for category in categories:
        category_name = category['category']
        items_in_category = conn.execute('SELECT * FROM items WHERE category = ? AND user_id = ? ORDER BY item_order', (category_name, current_user.id)).fetchall()
        processed_items = []
        for item in items_in_category:
            item_dict = dict(item)
            item_dict['tags'] = item_dict['tags'].split(',') if item_dict['tags'] else []
            processed_items.append(item_dict)
        items_by_category[category_name] = processed_items

    conn.close()
    return render_template('index.html', items_by_category=items_by_category, gpt_response=gpt_response, prompts=prompts, username=current_user.username)

def processItems(raw_item):
    item = re.sub(r'[^a-zA-Z0-9 ]+', '', raw_item.lower())
    item_singular = p.singular_noun(item) if p.singular_noun(item) else item
    return item_singular

@app.route('/update-item-name/<int:item_id>', methods=['POST'])
@login_required
def update_item_name(item_id):
    new_name = request.json['new_name'].strip()
    if not new_name:
        return jsonify({'status': 'error', 'message': 'Item name cannot be empty'}), 400
    new_name_singular = processItems(new_name)
    conn = get_db_connection()
    conn.execute('UPDATE items SET name = ? WHERE id = ? AND user_id = ?', (new_name_singular, item_id, current_user.id))
    conn.commit()
    conn.close()

    return jsonify({'status': 'success', 'message': 'Item name updated successfully'})

@app.route('/update-items', methods=['POST'])
@login_required
def update_items():
    data = request.json
    item_orders = data['items']

    conn = get_db_connection()
    for item in item_orders:
        item_id = int(item['id'].strip('item-'))  # Adjust as needed
        conn.execute('UPDATE items SET item_order = ?, category = ? WHERE id = ?', (item['order'], item['category'], item_id))
    conn.commit()
    conn.close()
    return 'OK', 200


@app.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete(item_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM items WHERE id = ? AND user_id = ?', (item_id, current_user.id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Item deleted successfully'})

@app.route('/ask-gpt4', methods=['GET','POST'])
@login_required
def ask_gpt4():
    data = request.get_json()
    selected_items = data['selected_items']
    selected_prompt = data['selected_prompt']

    system_message = prompts.get(selected_prompt, prompts["Detailed recipe"])
    openai.api_key = get_openai_api_key()

    if not selected_items:
         items_string = get_items_as_string()
    else:
         items_string = selected_items
         
    additional_instructions = []
    region = data['region']
    modifier = data['modifier']
    specifications = data['specifications']
    
    if region and region.strip():
        additional_instructions.append(f"Create something appropriate to {region}")
    if modifier and modifier.strip():
        additional_instructions.append(f"Create something that is {modifier}")
    if specifications and specifications.strip():
        additional_instructions.append(f"I very specifically want you to create {specifications}")

    additional_instructions_str = ", ".join(additional_instructions)

    if additional_instructions_str:
        system_message += f"\n\n{additional_instructions_str}"

    prompt_instruct = "Please refrain from including an opening or closing paragraph, just get right in to the recipes. The list of items I'd like you to use is: "
    combined_prompt = prompt_instruct + items_string
    print(system_message, combined_prompt)
    response = openai.chat.completions.create(
      model="gpt-4-turbo-preview",
      messages= [
        {"role":"system", "content": system_message},
        {"role": "user", "content": combined_prompt}
       ],
      max_tokens=800,
      temperature=0.8,
    )
    gpt_response = response.choices[0].message.content

    return jsonify({"gpt_response": gpt_response})

@app.route('/save-prompt', methods=['POST'])
@login_required  # Ensure that the user is logged in
def save_prompt():
    content = request.json['content']
    items = request.json['items']
    conn = get_db_connection()
    cursor = conn.execute('INSERT INTO prompts (content, items, user_id) VALUES (?, ?, ?)', (content, items, current_user.id))
    conn.commit()
    prompt_id = cursor.lastrowid  # Get the last inserted id
    conn.close()
    return jsonify({'status': 'success', 'message': 'Prompt saved successfully', 'prompt_id': prompt_id})

@app.route('/get-prompts', methods=['GET'])
@login_required
def get_prompts():
    conn = get_db_connection()
    prompts = conn.execute('SELECT * FROM prompts WHERE user_id = ? ORDER BY created_at DESC', (current_user.id,)).fetchall()
    conn.close()
    return jsonify([dict(prompt) for prompt in prompts])

@app.route('/delete-prompt/<int:prompt_id>', methods=['POST'])
@login_required
def delete_prompt(prompt_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM prompts WHERE id = ? AND user_id = ?', (prompt_id, current_user.id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Prompt deleted successfully'})

@app.route('/delete-item-from-prompt', methods=['POST'])
@login_required
def delete_item_from_prompt():
    data = request.json
    prompt_id = data['prompt_id']
    item_name = data['item_name']

    conn = get_db_connection()

    # Update prompt's item list
    current_items = conn.execute('SELECT items FROM prompts WHERE id = ?', (prompt_id,)).fetchone()
    if current_items:
        updated_items = [item for item in current_items['items'].split(',') if item.strip() != item_name]
        conn.execute('UPDATE prompts SET items = ? WHERE id = ?', (', '.join(updated_items), prompt_id))

    conn.execute('DELETE FROM items WHERE name = ? AND user_id = ?', (item_name, current_user.id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

# @app.route('/update-item-tags/<int:item_id>', methods=['POST'])
# @login_required
# def update_item_tags(item_id):
#     tags = request.json['tags']  # Expecting a list of tags
#     tags_str = ','.join(tags)  # Convert list of tags to a comma-separated string
#     conn = get_db_connection()
#     conn.execute('UPDATE items SET tags = ? WHERE id = ?', (tags_str, item_id))
#     conn.commit()
#     conn.close()
    
#     return jsonify({'status': 'success', 'message': 'Item tags updated successfully'})

@app.route('/update-item-tags-batch', methods=['POST'])
@login_required
def update_item_tags_batch():
    updates = request.json['updates']  # Expecting a dictionary of item_id: tags

    conn = get_db_connection()
    for item_id, tags in updates.items():
        tags_str = ','.join(tags)  # Convert list of tags to a comma-separated string
        conn.execute('UPDATE items SET tags = ? WHERE id = ?', (tags_str, item_id))
    
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Item tags updated successfully'})

if __name__ == '__main__':
    app.run()
