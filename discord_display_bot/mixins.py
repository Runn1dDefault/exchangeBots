class MessageMixin:
    DATABASE_ERROR_MSG = "```Some trouble at database```"
    CHANNEL_EXISTS_MSG = "```{}channel already exists in db```"
    CHANNEL_SUCCESS_ADD_MSG = "```Successfully saved channel to db```"
    CHANNEL_SUCCESS_REMOVE_MSG = "```Successfully remove channel from db```"
    TEMPLATE_SUCCESS_MSG = """
    ```Successfully get signals and saved!```
    """
    TEMPLATE_ERROR_MSG = """
                    ```
                    Your template does not match the template accepted by the bot,
                    please look carefully and compare with the test template: 
                    **Colon between key and value is required**
                    New:
                    Type: Future/No
                    Token: BTCUSDT
                    Direction: LONG
                    Entry: 222-333
                    Target1: 39500
                    Target2: 40000
                    Target3: 41000
                    Stop loss: 39000
                    Leverage: x20
                    ```
                    """
    TEMPLATE_ERROR_KEY_MSG = """
    ```message is missing one of the required keys or incorrect key, carefully look and resend check template, message 
    required this keys {}
    ```
    """

    CHANNEL_IS_NOT_ACTIVATE_MSG = """
    ```Error! {channel_name} channel is not activate in db, please activate channel with command {activate}```
    """
