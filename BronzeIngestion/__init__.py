import logging
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('--- DEBUG START ---')
    try:
        # Step 1: Test basic imports one by one
        logging.info("Testing pandas import...")
        import pandas as pd
        logging.info("✅ Pandas loaded")

        logging.info("Testing cryptography import...")
        from cryptography.fernet import Fernet
        logging.info("✅ Cryptography loaded")

        logging.info("Testing sqlalchemy import...")
        from sqlalchemy import create_engine
        logging.info("✅ SQLAlchemy loaded")

        return func.HttpResponse("🚀 All libraries loaded successfully! The environment is healthy.", status_code=200)

    except ImportError as e:
        logging.error(f"❌ LIBRARY MISSING: {str(e)}")
        return func.HttpResponse(f"Missing Library: {str(e)}", status_code=500)
    except Exception as e:
        logging.error(f"❌ General Error: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)




