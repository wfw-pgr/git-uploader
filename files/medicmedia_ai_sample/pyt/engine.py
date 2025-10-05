import os, sys, json
import google.genai


# ========================================================= #
# === hit__api.py                                         === #
# ========================================================= #

def hit__api( inpFile="dat/database.json", chat_log=[] ):

    # ------------------------------------------------- #
    # --- [0] parameters                            --- #
    # ------------------------------------------------- #
    gemini_model  = "gemini-2.5-flash"
    max_sentences = 3
    system        = f"""あなたは以下のJSONで定義されたキャラクターとしてロールプレイを行います。次のJSON設定を読み込み、内容をすべて「キャラクターの行動規範」として採用してください。以後の会話では、この設定を維持してロールプレイを続けてください。ルール:
- 常に患者キャラクターになりきり、常に一人称で発話する。
- 一度の返答は {max_sentences} 文以内.
- 会話ログ([chat_log])は過去の会話を示す．<D>は医者側、<P>は患者側の発言を示す．過去の発言を考慮し、一貫性のある回答をする．\n"""
    
    # ------------------------------------------------- #
    # --- [1] load database.json                    --- #
    # ------------------------------------------------- #
    with open( inpFile, "r" ) as f:
        db = json.load( f )

    # ------------------------------------------------- #
    # --- [2] prompt make                           --- #
    # ------------------------------------------------- #
    patient   = json.dumps( db["case002"], ensure_ascii=False, indent=2 )
    chat_dump = "\n".join( chat_log )
    prompt    = f"""[system]\n{system}\n\n[patient]\n{patient}\n\n[chat_log]\n{chat_dump}"""

    # ------------------------------------------------- #
    # --- [3] hit                                   --- #
    # ------------------------------------------------- #
    api_key   = os.environ.get( "GEMINI_API_KEY" )
    client    = google.genai.Client( api_key=api_key )
    response  = client.models.generate_content( model=gemini_model, contents=prompt )
    
    # ------------------------------------------------- #
    # --- [4] return                                --- #
    # ------------------------------------------------- #
    return( ( prompt, response.text ) )


# ========================================================= #
# ===  chat__usingTerminal                              === #
# ========================================================= #
def chat__usingTerminal():

    max_chats  = 10
    chat_log   = []
    
    # ------------------------------------------------- #
    # --- [1] wait input                            --- #
    # ------------------------------------------------- #
    for imsg in range( max_chats):
        print( "[in]  >> ", end="" )
        input_sentence   = input()
        chat_log        += [ "<D> " + input_sentence ]
        prompt, response = hit__api( chat_log=chat_log )
        chat_log        += [ "<P> " + response ]
        print( "[out] >> {}".format( response ) )
    
    # ------------------------------------------------- #
    # --- [2]                         --- #
    # ------------------------------------------------- #
    


# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    # prompt, response = hit__api()
    # print( prompt, response )

    chat__usingTerminal()
