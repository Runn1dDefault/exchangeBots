from models import CustomerTask, Exchange, DBUser, TraderTask, db


def save_data(model, *args, **kwargs):
    with db.atomic() as txn:
        try:
            obj = model.create(**kwargs)
        except Exception as e:
            txn.rollback()
            print('Function "save_data" :', e.args)
        else:
            txn.commit()
            return obj


def save_channel(model, type_src, channel_id, name):
    return save_data(
        model, type_src=type_src, channel_id=channel_id, name=name
    )


def search_and_format_target(**kwargs):
    return ','.join([value for key, value in kwargs.items() if 'target' in key])
    # targets = ""
    #
    # for key, value in kwargs.items():
    #     if 'target' in key:
    #         targets = targets + ',' + value
    # return targets


def divide_entry(entry):
    entry_min, entry_max = entry.split('-')
    return entry_min, entry_max


def save_trader_task(model, channel_id, **kwargs):
    trader_type = None
    token = kwargs.get('token')
    direction = kwargs.get('direction')
    entry_min, entry_max = divide_entry(kwargs.get('entry'))
    stop_loss = kwargs.get('stop loss')
    targets = search_and_format_target(**kwargs)
    leverage = int(kwargs.get('leverage').replace('x', ''))
    status = None
    return save_data(model, channel_id=channel_id, token=token, direction=direction,
                     entry_min=entry_min, entry_max=entry_max, stop_loss=stop_loss,
                     targets=targets, leverage=leverage)


def save_customer_task(channel_id, **kwargs):
    api_reserve = None
    with db:
        kwargs['leverage'] = TraderTask.get(channel_id=channel_id, type_src='discord').leverage \
            if kwargs.get('leverage') is None else kwargs['leverage'].replace('x', '')
        db_user = DBUser.get_or_none(id=1),  # TODO: change after added logic for discord channel consumers
        exchange = Exchange.get(name=kwargs['exchange'])
    return save_data(CustomerTask,
                     user=db_user,
                     channel_id=channel_id,
                     exchange=exchange,
                     api_key=kwargs['public key'].strip(), api_secret=kwargs['private key'].strip(),
                     api_passphrase=kwargs.get('passphrase'),
                     percent_portfolio=kwargs['percent of portfolio'],
                     leverage=kwargs['leverage']
                     )


def check_exist(model, channel_id):
    is_exists = False
    with db:
        query = model.select().where(model.channel_id == channel_id)
        if query.exists():
            is_exists = True
    return is_exists


def get_db_object(model, channel_id):
    with db:
        return model.get(model.channel_id == channel_id)


def remove_channel(model, channel_id) -> None:
    with db.atomic() as txn:
        try:
            model.delete().where(
                model.channel_id == channel_id
            ).execute()
        except Exception as e:
            txn.rollback()
            print('Method "remove_channel": ', e.args)
        else:
            txn.commit()
