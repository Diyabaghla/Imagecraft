from flask import Blueprint, render_template, request, jsonify
import re
import long_responses as long

# Create Blueprint
chatbot_bp = Blueprint(
    "chatbot", __name__,
    template_folder="templates",
    static_folder="static"
)

# ---------------- Helper Functions ----------------
def message_probability(user_message, recognised_words, single_response=False, required_words=[]):
    message_certainty = 0
    has_required_words = True

    for word in user_message:
        if word in recognised_words:
            message_certainty += 1

    percentage = float(message_certainty) / float(len(recognised_words)) if recognised_words else 0

    for word in required_words:
        if word not in user_message:
            has_required_words = False
            break

    return int(percentage * 100) if has_required_words or single_response else 0


def check_all_messages(message):
    highest_prob_list = {}

    def response(bot_response, list_of_words, single_response=False, required_words=[]):
        nonlocal highest_prob_list
        highest_prob_list[bot_response] = message_probability(message, list_of_words, single_response, required_words)

    # Core commands
    response(long.R_WELCOME, ['hello', 'hi', 'hey'], single_response=True)
    response(long.R_HELP, ['help', 'assist', 'what', 'can', 'you', 'do'], required_words=['help'])

    # Captioning
    response(long.R_CAPTION_HELP, ['caption', 'image', 'description'], required_words=['caption'])
    response(long.R_CAPTION_EXAMPLE, ['example', 'caption', 'image'], required_words=['caption', 'example'])

    # Sketching
    response(long.R_SKETCH_HELP, ['sketch', 'pencil', 'drawing'], required_words=['sketch'])
    response(long.R_SKETCH_TIPS, ['tips', 'sketch', 'quality'], required_words=['sketch', 'tip'])

    # Features
    response(long.R_FEATURES, ['features', 'tools', 'available'], required_words=['features'])

    # Support
    response(long.R_SUPPORT, ['error', 'problem', 'upload', 'issue'], required_words=['error'])
    response(long.R_THANKS, ['thanks', 'thank', 'appreciate'], single_response=True)

    # Fun & fallback
    response(long.R_FUN_FACT, ['fact', 'ai', 'image'], required_words=['fact'])
    response(long.R_MOTIVATION, ['motivation', 'quote', 'encouragement'], required_words=['motivation'])

    best_match = max(highest_prob_list, key=highest_prob_list.get)
    return long.unknown() if highest_prob_list[best_match] < 1 else best_match


def get_response(user_input):
    split_message = re.split(r'\s+|[,;?!.-]\s*', user_input.lower())
    return check_all_messages(split_message)


# ---------------- Routes ----------------
@chatbot_bp.route("/chatbot")
def home():
    return render_template("chatbot_index.html")   # loads template

@chatbot_bp.route("/get", methods=["POST"])
def chatbot_response():
    user_text = request.form.get("msg", "")
    response_text = get_response(user_text)
    return jsonify({"response": response_text})


