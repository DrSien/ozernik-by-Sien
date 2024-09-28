import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='.', intents=intents)


'''Создание войса'''

voice_list = [] #Список созданных каналов
@bot.event
async def on_voice_state_update(member, before, after):
    try:
        with open(f'CVid {member.guild.name}.txt', 'r') as f:
            creator_voice_id = int(f.readlines()[0][:-1])
        try:
            if (not before.channel.members) and (before.channel.id in voice_list):
                await before.channel.delete()
                voice_list.remove(before.channel.id)
            if after.channel.id == creator_voice_id:
                channel = await member.guild.create_voice_channel(name = f'Канал {member.display_name}', category = member.voice.channel.category)
                await channel.send('Используйте `/rename` для смены названия голосового канала')
                voice_list.append(channel.id)
                await member.move_to(channel)
        except:
            if after.channel.id == creator_voice_id:
                channel = await member.guild.create_voice_channel(name = f'Канал {member.display_name}', category = member.voice.channel.category)
                await channel.send('Используйте `/rename` для смены названия голосового канала')
                voice_list.append(channel.id)
                await member.move_to(channel)
    except:
        if (not before.channel.members) and (before.channel.id in voice_list):
            await before.channel.delete()
            voice_list.remove(before.channel.id)
            
@bot.tree.command(name='войскреатор', description='Установить канал из которого создаётся войс')
@discord.app_commands.rename(voice = 'канал', role = 'роль')
@discord.app_commands.describe(voice = 'Исходный канал из которого создаются другие', role = 'Роль, которой можно менять название созданного канала')
async def CV_settings(interaction: discord.Interaction, voice: discord.VoiceChannel, role: discord.Role):
    if interaction.user.guild_permissions.administrator == True:
        with open(f'CVid {interaction.guild.name}.txt', 'w') as f:
            f.writelines('%d' % voice.id +'\n'+ '%d' % role.id)
        await interaction.response.send_message(f'Теперь при подключении к {voice.mention} будет создаваться новый канал\nУчастники с ролью {role.mention} смогут менять название созданного канала')
    else:
        await interaction.response.send_message('У вас недостаточно прав чтобы использовать эту команду', ephemeral=True)
        
# Команда для смены названия
@bot.tree.command(name='rename', description='Меняет название голосового канала')
@discord.app_commands.rename(new_name = 'название')
@discord.app_commands.describe(new_name = 'Новое название канала')
async def rename_voice(interaction: discord.Interaction, new_name:str):
    try:
        with open(f'CVid {interaction.guild.name}.txt', 'r') as f:
                rename_role_id = int(f.readlines()[1])
        if interaction.guild.get_role(rename_role_id) in interaction.user.roles:
            if interaction.channel.id in voice_list:
                await interaction.channel.edit(name = new_name)
                await interaction.response.send_message(f'{interaction.user.display_name} меняет название канала на **{new_name}**')
            else:
                await interaction.response.send_message('Нельзя изменить название этого канала', ephemeral=True)
        else:
            await interaction.response.send_message(f'Изменить название канала может только {interaction.guild.get_role(rename_role_id).mention}',ephemeral=True)
    except:
        await interaction.response.send_message('Эта команда ещё не настроена', ephemeral=True)


'''Передача дуэлянта'''

## Список ролей
duel_1 = set()
duel_2 = set()
duel_3 = set()
duel_4 = set()
duel_5 = set()
duel_role_list = set()
def set_dl():
    global duel_1
    global duel_2
    global duel_3
    global duel_4
    global duel_5
    global duel_role_list
    duel_1 = bot.get_guild(1189392542152798279).get_role(1272833031669026836)# 1 уровень
    duel_2 = bot.get_guild(1189392542152798279).get_role(1272833131719688242)# 2 уровень
    duel_3 = bot.get_guild(1189392542152798279).get_role(1272833236065714196)# 3 уровень
    duel_4 = bot.get_guild(1189392542152798279).get_role(1272833279393009736)# 4 уровень
    duel_5 = bot.get_guild(1189392542152798279).get_role(1272833322241888308)# 5 уровень

    duel_role_list = [duel_1, duel_2, duel_3, duel_4, duel_5]#список ролей (1-5 ур)

## Определитель
def is_duelist(roles):
    for role in roles:
        if role in duel_role_list:
            return role

## Передача
class tr():
    free = True
    duelist_1 = set()
    duelist_2 = set()
    duelist_role_1 = set()
    duelist_role_2 = set()

# Представление запроса о передачи
class confirm_transfer(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
    @discord.ui.button(label='Принять', style=discord.ButtonStyle.green)
    async def accept_transfer(self, interaction:discord.Interaction, button:discord.ui.Button):
        if interaction.user != tr.duelist_2:
            # отказ ненужному лицу
            await interaction.response.send_message(f'Принять предложение может только {tr.duelist_2.mention}', ephemeral=True)
        else:
            ### непосредственно передача
            ## определение какие роли выдать

            # новая роль для д1
            if tr.duelist_role_1 != duel_1:
                await tr.duelist_1.add_roles(duel_role_list[duel_role_list.index(tr.duelist_role_1)-1])
            await tr.duelist_1.remove_roles(tr.duelist_role_1)

            # новая роль для д2
            if tr.duelist_role_2 == None:
                await tr.duelist_2.add_roles(duel_1)
            else:
                await tr.duelist_2.add_roles(duel_role_list[duel_role_list.index(tr.duelist_role_2)+1])
                await tr.duelist_2.remove_roles(tr.duelist_role_2)

            # разрешает новые запросы
            tr.free = True

            await interaction.response.edit_message(content='Роль передана!', view=None)

    @discord.ui.button(label='Отменить', style=discord.ButtonStyle.red)
    async def cancel_transfer(self, interaction:discord.Interaction, button:discord.ui.Button):
        if (interaction.user == tr.duelist_1) or (interaction.user == tr.duelist_2):
            # отмена текущей передачи и разрешение новых
            await interaction.response.edit_message(content='Передача отменена.', view=None)
            tr.free = True
        else:
            # отказ ненужному лицу
            await interaction.response.send_message(f'Отменить передачу могут только {tr.duelist_1.mention} и {tr.duelist_2.mention}', ephemeral=True)

    # разрешает новые запросы
    def on_timeout(self):
        tr.free = True

# Команда для запроса
transfer_group = app_commands.Group(name='transfer', description='...')
@transfer_group.command(name="duelist", description='Передать уровень дуэлянта другому человеку')
@app_commands.rename(recipient='получатель')
@app_commands.describe(recipient='Человек, который получит от вас уровень дуэлянта')
async def transfer (interaction:discord.Interaction, recipient:discord.Member):
    d1_role = is_duelist(interaction.user.roles)
    d2_role = is_duelist(recipient.roles)
    if interaction.user != recipient:
        if tr.free == True:
            if d1_role:
                if d2_role != duel_5:
                    tr.free = False# блокирует новые запросы
                    tr.duelist_1, tr.duelist_2 = interaction.user, recipient
                    tr.duelist_role_1, tr.duelist_role_2 = d1_role, d2_role
                    await interaction.response.send_message(f'{tr.duelist_1.mention} хочет передать уровень дуэлянта {tr.duelist_2.mention}', view = confirm_transfer(), delete_after = 60)
                else:
                    await interaction.response.send_message('Отправка невозможна. У получателя уже максимальный уровень', ephemeral=True)
            else:
                await interaction.response.send_message('Вы не дуэлянт, и поэтому не можете использовать эту команду', ephemeral=True)
        else:
            await interaction.response.send_message('Передача роли сейчас невозможна. Попробуйте позже', ephemeral=True)
    else:
        await interaction.response.send_message('Интересный ход, но вы не можете передать роль самому себе', ephemeral=True)

async def on_ready():
    bot.tree.add_command(transfer_group)
    await bot.tree.sync()
