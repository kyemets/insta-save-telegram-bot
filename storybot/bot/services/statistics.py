@router.message(Command('stats'))
async def stats(msg: Message):
    pipeline = [
        {'$match': {'user_id': msg.from_user.id}},
        {'$group': {'_id': None, 'total': {'$sum': '$sent'}}}
    ]
    agg = await StatsDAO.coll.aggregate(pipeline).to_list(1)
    total = agg[0]['total'] if agg else 0
    await msg.answer(f"📊 Всего отправлено историй: *{total}*", parse_mode='Markdown')
