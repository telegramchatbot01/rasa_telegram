# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from typing import Any, Text, Dict, List

from requests import NullHandler

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.events import AllSlotsReset, UserUtteranceReverted
import mysql.connector
from rasa_sdk.executor import CollectingDispatcher
import qrcode
from PIL import Image, ImageDraw, ImageFont
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

def connect_db(hote, usr, pwd, db) :
    conn_main = mysql.connector.connect(
        host = hote,
        user = usr,
        password = pwd,
        database = db
    )  
    if (conn_main) : 
        print("connected succesfully !")
        return conn_main
    else : 
        print("Failed !")
        return -1

def select_from_where_one(connection, table_name, key, value) : 
    sql_req = 'SELECT * FROM {} WHERE {} = "{}"'.format(
        table_name, 
        key, 
        value)
    cursor = connection.cursor()
    cursor.execute(sql_req)
    records = cursor.fetchone()
    
    if records: 
        columnNames = [column[0] for column in cursor.description]
        rows_dict = dict(zip(columnNames , records))
        return rows_dict
    else : 
        print("Désolé je peux trouver un laboratoire veuillez choisir un autre titre !")
        return None

def select_from_where(connection, table_name, key, value) : 
    sql_req = 'SELECT * FROM {} WHERE {} = "{}"'.format(
        table_name, 
        key, 
        value)
    cursor = connection.cursor()
    cursor.execute(sql_req)
    records = cursor.fetchall()
    
    if records: 
        ret_array = []
        for record in records : 
            columnNames = [column[0] for column in cursor.description]
            rows_dict = dict(zip(columnNames , record))
            ret_array.append(rows_dict)
        return ret_array
    else : 
        print("Désolé je peux trouver un laboratoire veuillez choisir un autre titre !")
        return None
    

def select_from_all(connection, table_name) : 
    sql_req = 'SELECT * FROM {}'.format(table_name)
    
    cursor = connection.cursor()
    cursor.execute(sql_req)
    records = cursor.fetchall()
    
    if records : 
        insertObject = []
        columnNames = [column[0] for column in cursor.description]
        for record in records:
            insertObject.append( dict( zip( columnNames , record ) ) )
        return insertObject
    else : 
        print("Désolé je peux trouver un laboratoire veuillez choisir un autre titre !")
        return None

def qr_card(code) : 
    
    qr = qrcode.QRCode()
    qr.add_data(code)
    qr.make()
    img_qr = qr.make_image()
    img_qr = img_qr.resize((300, 300))
    
    #init empty 
    img_text = Image.new('RGB', (300, 100), color = (240, 240, 240))
    
    #fonts import
    font_bold = ImageFont.truetype(r'fonts\OpenSans-ExtraBold.ttf', 25) 
    font_regular = ImageFont.truetype(r'fonts\OpenSans-LightItalic.ttf', 15) 
    font_small = ImageFont.truetype(r'fonts\OpenSans-LightItalic.ttf', 7) 
    
    #write on img
    d = ImageDraw.Draw(img_text)
    d.text((10,5), "Bonjour,", font = font_regular, fill=(0,0,0))
    d.text((10,25), "Votre code de suivi est : ", font = font_regular, fill=(0,0,0))
    d.text((10,45), "{}".format(code), font = font_bold, fill=(0,0,0), align ="center")
    d.text((10,80), "Merci pour votre confiance, pour reclamation veuillez contacter notre service", font = font_small, fill=(0,0,0))
    d.text((10,90), "client contact@mystore.com", font = font_small, fill=(0,0,0))
    
    #combine the images
    new_image = Image.new('RGB',(img_text.size[0], 400), (250,250,250))
    new_image.paste(img_text)
    new_image.paste(img_qr,(0,100))
    
    path = "imgs/{}.png".format(code)
    new_image.save(path)
    return path

def send_email(receiver_email, path):

    with open(path, "rb") as image_file:
        data = image_file.read()

    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "sender@gmail.com"

    context = ssl.create_default_context()
    message = MIMEMultipart("alternative")
    message["Subject"] = "Demande de renvoyer le bon d'achat"
    message["From"] = sender_email
    message["To"] = receiver_email
    img = MIMEImage(data, name="Document")

    html = """\
    <html>
    <body>
        <p>Salut,<br>
        Vous venez de demander à vous envoyer votre document, veuillez trouver ci-joint le document bigsmile :<br>
        Cordialement 
        </p>
    </body>
    </html>
    """
    part2 = MIMEText(html, "html")
    message.attach(part2)
    message.attach(img)
    
    try : 
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, "pass")
            server.sendmail(sender_email, receiver_email, message.as_string())
        return "Envoyé"
    except : 
        return "problème d'envoi, réessayez ultérieurement !"
    

############################################################################################
############################################################################################
############################################################################################
############################################################################################

class QueryCodes(Action):

    def name(self) -> Text:
        return "query_codes"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        #connect to the database 
        connection = connect_db("127.0.0.1", "root", "", "rasa")
        #get the value 
        value = tracker.get_slot("track_code")
        #select data
        get_query_results = select_from_where(connection, "codes", "codes", value)
        print(get_query_results)
        dispatcher.utter_message(text="L'etat de votre commande est  ==> {}".format(get_query_results[0]["satus"]))

        return [AllSlotsReset()]


class QueryOffers(Action):

    def name(self) -> Text:
        return "query_offers"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        #connect to the database 
        connection = connect_db("127.0.0.1", "root", "", "rasa")

        #select data
        get_query_results = select_from_all(connection, "promos") 

        strings = ["{} : {}".format(element["promo"], element["validite"]) for element in get_query_results]
        output = "\n".join(strings)

        dispatcher.utter_message(text=output)

        return [AllSlotsReset()]

class CodeCard(Action):

    def name(self) -> Text:
        return "code_card"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        #connect to the database 
        connection = connect_db("127.0.0.1", "root", "", "rasa")
        #get the value 
        value = tracker.get_slot("track_code2")
        reciever = tracker.get_slot("email")
        print("value")
        #verify if the code exists 
        if(select_from_where(connection, "codes", "codes", value)) : 
            path = qr_card(value)
            resp = send_email(reciever, path)
            dispatcher.utter_message(text=resp)

        else : 
            dispatcher.utter_message(text="Le code que vous avez renseigner n'existe pas !")
        
        return [AllSlotsReset()]

class Start(Action):

    def name(self) -> Text:
        return "start"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

            dispatcher.utter_message(text="Bonjour, je suis un robot de Bigsmile, prêt à répondre à vos questions ! \nvous pouvez commencer la conversation en disant 'jai besoin d'aide'")
        
            return []


class ValidateTrackCodeForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_track_code_form"

    @staticmethod
    def country_code() -> List[Text]:
        """Database of supported keys formation"""
        return ["ma", "fr", "es", "us", "uk"]


    def validate_track_code(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]: 

        """Validate track_code value."""
        print(value)
        if len(value) == 10: 
            return {"track_code": value}
        else :
            dispatcher.utter_message(text = "Le code que vous avez saisie n'est pas valide !")
            return {"track_code": None}

class ValidateQrCodeForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_qr_code_form"

    @staticmethod
    def country_code() -> List[Text]:
        """Database of supported keys"""
        return ["ma", "fr", "es", "us", "uk"]


    def validate_track_code(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]: 

        """Validate track_code value."""
        print(value)
        if len(value) == 10: 
            return {"track_code2": value}
        else :
            dispatcher.utter_message(text = "Le code que vous avez saisie n'est pas valide !")
            return {"track_code2": None}