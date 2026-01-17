from decouple import config

def sending_email(*, subject, email, message):
    if (config("ENVIRONMENT") == "PROD"): 
        pass 
    else: 
        pass 

def sending_sms(message, phone):
    if (config("ENVIRONMENT") == "PROD"):
        pass
    else:
        pass