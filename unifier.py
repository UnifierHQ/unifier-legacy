"""
Unifier Legacy - A "simple" bot to unite Discord servers with webhooks
Copyright (C) 2023  Green

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import discord
from discord.ext import commands
import ast
import aiofiles
import hashlib
bot = commands.Bot(command_prefix='u!',intents=discord.Intents.all())

mentions = discord.AllowedMentions(everyone=False,roles=False,users=False)

rules = {
    '_main': ['Be civil and follow Discord ToS and guidelines.',
              'Absolutely no NSFW in here - this is a SFW channel.',
              'Don\'t be a dick and harass others, be a nice fellow to everyone.',
              'Don\'t cause drama, we like to keep things clean.',
              'Don\'t ask for punishments, unless you want to be restricted.',
              'Server and global moderators have the final say, don\'t argue unless there\'s a good reason to.',
              'These rules are not comprehensive - don\'t use loopholes or use "it wasn\'t in the rules" as an argument.'
              ],
    '_pr': ['Follow all main room rules.',
            'Only PRs in here - no comments allowed.'],
    '_prcomments': ['Follow all main room rules.',
                    'Don\'t make PRs in here - this is for comments only.'],
    '_liveries': ['Follow all main room rules.',
                  'Please keep things on topic and post liveries or comments on liveries only.']
    }

def encrypt_string(hash_string):
    sha_signature = \
        hashlib.sha256(hash_string.encode()).hexdigest()
    return sha_signature

@bot.event
async def on_ready():
    print('ready hehe')

@bot.command(aliases=['link','connect','federate','bridge'])
async def bind(ctx,*,room=''):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send('You don\'t have the necessary permissions.')
    roomid = '_'+room
    if room=='':
        roomid = '_main'
    try:
        async with aiofiles.open(f'participants{roomid}.txt','r',encoding='utf-8') as x:
            data = await x.read()
            data = ast.literal_eval(data)
            await x.close()
    except:
        return await ctx.send('This isn\'t a valid room. Try `main`, `pr`, `prcomments`, or `liveries` instead.')
    try:
        try:
            guild = data[f'{ctx.guild.id}']
        except:
            guild = []
        if len(guild) >= 1:
            return await ctx.send('Your server is already linked to this room.\n**Accidentally deleted the webhook?** `u!unlink` it then `u!link` it back.')
        index = 0
        text = ''
        for rule in rules[roomid]:
            if text=='':
                text = f'1. {rule}'
            else:
                text = f'{text}\n{index}. {rule}'
            index += 1
        text = f'{text}\n\nPlease display these rules somewhere accessible.'
        embed = discord.Embed(title='Please agree to the room rules first:',description=text)
        embed.set_footer(text='Failure to follow room rules may result in user or server restrictions.')
        ButtonStyle = discord.ButtonStyle
        row = [
            discord.ui.Button(style=ButtonStyle.green, label='Accept and bind', custom_id=f'accept',disabled=False),
            discord.ui.Button(style=ButtonStyle.red, label='No thanks', custom_id=f'reject',disabled=False)
            ]
        btns = discord.ui.ActionRow(row[0],row[1])
        components = discord.ui.MessageComponents(btns)
        msg = await ctx.send(embed=embed,components=components)

        def check(interaction):
            return interaction.user.id==ctx.author.id and (
                interaction.custom_id=='accept' or
                interaction.custom_id=='reject'
                ) and interaction.channel.id==ctx.channel.id

        try:
            resp = await bot.wait_for("component_interaction", check=check, timeout=60.0)
        except:
            row[0].disabled = True
            row[1].disabled = True
            btns = discord.ui.ActionRow(row[0],row[1])
            components = discord.ui.MessageComponents(btns)
            await msg.edit(components=components)
            return await ctx.send('Timed out.')
        row[0].disabled = True
        row[1].disabled = True
        btns = discord.ui.ActionRow(row[0],row[1])
        components = discord.ui.MessageComponents(btns)
        await resp.response.edit_message(components=components)
        if resp.custom_id=='reject':
            return
        webhook = await ctx.channel.create_webhook(name='Unifier')
        async with aiofiles.open(f'participants{roomid}.txt','r',encoding='utf-8') as x:
            data = await x.read()
            data = ast.literal_eval(data)
            await x.close()
        guild = []
        guild.append(webhook.id)
        data.update({f'{ctx.guild.id}':guild})
        x = open(f'participants{roomid}.txt','w+',encoding='utf-8')
        x.write(f'{data}')
        x.close()
        await ctx.send('Linked channel with network!')
    except:
        await ctx.send('Something went wrong - check my permissions.')
        raise

@bot.command(aliases=['unlink','disconnect'])
async def unbind(ctx,*,room=''):
    if room=='':
        return await ctx.send('You must specify the room to unbind from.')
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send('You don\'t have the necessary permissions.')
    roomid = '_'+room
    try:
        async with aiofiles.open(f'participants{roomid}.txt','r',encoding='utf-8') as x:
            data = await x.read()
            data = ast.literal_eval(data)
            await x.close()
    except:
        return await ctx.send('This isn\'t a valid room. Try `main`, `pr`, `prcomments`, or `liveries` instead.')
    try:
        try:
            hooks = await ctx.guild.webhooks()
        except:
            return await ctx.send('I cannot manage webhooks.')
        hook_ids = data.setdefault(f'{ctx.guild.id}', [])
        for webhook in hooks:
            if webhook.id in hook_ids:
                await webhook.delete()
                break
        data.pop(f'{ctx.guild.id}')
        x = open(f'participants{roomid}.txt','w+',encoding='utf-8')
        x.write(f'{data}')
        x.close()
        await ctx.send('Unlinked channel from network!')
    except:
        await ctx.send('Something went wrong - check my permissions.')
        raise

@bot.command(aliases=['ban'])
async def restrict(ctx,*,target):
    if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.kick_members or
            ctx.author.guild_permissions.ban_members):
        return await ctx.send('You cannot restrict members.')
    try:
        userid = int(target.replace('<@','',1).replace('!','',1).replace('>','',1))
    except:
        return await ctx.send('Invalid user!')
    try:
        async with aiofiles.open(f'{ctx.guild.id}_bans.txt','r',encoding='utf-8') as x:
            banlist = await x.read()
            banlist = ast.literal_eval(banlist)
            await x.close()
    except:
        banlist = []
    if userid in banlist:
        return await ctx.send('User already banned!')
    banlist.append(userid)
    x = open(f'{ctx.guild.id}_bans.txt','w+',encoding='utf-8')
    x.write(f'{banlist}')
    x.close()
    await ctx.send('User can no longer forward messages to this channel!')

@bot.command(aliases=['unban'])
async def unrestrict(ctx,*,target):
    if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.kick_members or
            ctx.author.guild_permissions.ban_members):
        return await ctx.send('You cannot unrestrict members.')
    try:
        userid = int(target.replace('<@','',1).replace('!','',1).replace('>','',1))
    except:
        return await ctx.send('Invalid user!')
    try:
        async with aiofiles.open(f'{ctx.guild.id}_bans.txt','r',encoding='utf-8') as x:
            banlist = await x.read()
            banlist = ast.literal_eval(banlist)
            await x.close()
    except:
        banlist = []
    if not userid in banlist:
        return await ctx.send('User not banned!')
    banlist.remove(userid)
    x = open(f'{ctx.guild.id}_bans.txt','w+',encoding='utf-8')
    x.write(f'{banlist}')
    x.close()
    await ctx.send('User can now forward messages to this channel!')

@bot.command(aliases=['find'])
async def identify(ctx):
    if not ctx.author.id==356456393491873795:
        return
    async with aiofiles.open(f'participants_main.txt','r',encoding='utf-8') as x:
        data = await x.read()
        await x.close()
    async with aiofiles.open(f'participants_pr.txt','r',encoding='utf-8') as x:
        data1 = await x.read()
        await x.close()
    async with aiofiles.open(f'participants_prcomments.txt','r',encoding='utf-8') as x:
        data2 = await x.read()
        await x.close()
    async with aiofiles.open(f'participants_liveries.txt','r',encoding='utf-8') as x:
        data3 = await x.read()
        await x.close()
    try:
        msg = ctx.message.reference.cached_message
        if msg==None:
            msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    except:
        return await ctx.send('Invalid message!')
    if msg.webhook_id==None or (not f'{msg.webhook_id}' in data and
                                not f'{msg.webhook_id}' in data1 and
                                not f'{msg.webhook_id}' in data2 and
                                not f'{msg.webhook_id}' in data3):
        return await ctx.send('I didn\'t forward this!')
    identifier = msg.author.name.split('(')
    identifier = identifier[len(identifier)-1].replace(')','')
    username = msg.author.name[:-9]
    found = False
    origin_guild = None
    origin_user = None
    for guild in bot.guilds:
        hashed = encrypt_string(f'{guild.id}')
        guildhash = identifier[3:]
        if hashed.startswith(guildhash):
            origin_guild = guild
            userhash = identifier[:-3]
            try:
                matches = list(filter(lambda x: encrypt_string(f'{x.id}').startswith(userhash), guild.members))
                if len(matches)==1:
                    origin_user = matches[0]
                else:
                    if len(matches==0):
                        raise ValueError()
                    text = f'Found multiple matches for {origin_guild.name} ({origin_guild.id})'
                    for match in matches:
                        text = text + '\n{match} ({match.id})'
                    return await ctx.send(text)
                found = True
            except:
                continue
    
    if found:
        await ctx.send(f'{origin_user} ({origin_user.id}) via {origin_guild.name} ({origin_guild.id})')
    else:
        await ctx.send('Could not identify user!')

@bot.event
async def on_message(message):
    if not message.webhook_id==None:
        # webhook msg
        return

    if message.content.startswith('u!'):
        if not message.author.id==356456393491873795:
            return
        return await bot.process_commands(message)
    
    async with aiofiles.open(f'participants_main.txt','r',encoding='utf-8') as x:
        data = await x.read()
        data = ast.literal_eval(data)
        await x.close()

    async with aiofiles.open(f'participants_pr.txt','r',encoding='utf-8') as x:
        data2 = await x.read()
        data2 = ast.literal_eval(data2)
        await x.close()

    async with aiofiles.open(f'participants_prcomments.txt','r',encoding='utf-8') as x:
        data3 = await x.read()
        data3 = ast.literal_eval(data3)
        await x.close()

    async with aiofiles.open(f'participants_liveries.txt','r',encoding='utf-8') as x:
        data4 = await x.read()
        data4 = ast.literal_eval(data4)
        await x.close()

    if (not f'{message.guild.id}' in data and
        not f'{message.guild.id}' in data2 and
        not f'{message.guild.id}' in data3 and
        not f'{message.guild.id}' in data4) or message.author.id==1187093090415149056:
        return

    try:
        hooks = await message.channel.webhooks()
    except:
        return
    found = False
    hook_ids = data.setdefault(f'{message.guild.id}', [])
    hook_ids_2 = data2.setdefault(f'{message.guild.id}', [])
    hook_ids_3 = data3.setdefault(f'{message.guild.id}', [])
    hook_ids_4 = data4.setdefault(f'{message.guild.id}', [])
    origin_room = 0
    
    for webhook in hooks:
        if webhook.id in hook_ids:
            origin_room = 0
            found = True
            break
        elif webhook.id in hook_ids_2:
            origin_room = 1
            data = data2
            found = True
            break
        elif webhook.id in hook_ids_3:
            origin_room = 2
            data = data3
            found = True
            break
        elif webhook.id in hook_ids_4:
            origin_room = 3
            data = data4
            found = True
            break

    if not found:
        return

    user_hash = encrypt_string(f'{message.author.id}')[:3]
    guild_hash = encrypt_string(f'{message.guild.id}')[:3]
    identifier = user_hash + guild_hash

    for key in data:
        if int(key)==message.guild.id:
            continue
        try:
            async with aiofiles.open(f'{key}_bans.txt','r',encoding='utf-8') as x:
                banlist = await x.read()
                banlist = ast.literal_eval(banlist)
                await x.close()
        except:
            banlist = []
        if message.author.id in banlist:
            continue
        hook_ids = data.setdefault(key, [])
        sent = False
        guild = bot.get_guild(int(key))
        try:
            hooks = await guild.webhooks()
        except:
            continue
        for webhook in hooks:
            if webhook.id in hook_ids:
                try:
                    url = message.author.avatar.url
                except:
                    url = None
                files = []
                index = 0
                for attachment in message.attachments:
                    if (not 'audio' in attachment.content_type and not 'video' in attachment.content_type and
                        not 'image' in attachment.content_type):
                        continue
                    file = await attachment.to_file(use_cached=True,spoiler=attachment.is_spoiler())
                    files.append(file)
                    index += 1
                if not message.reference==None:
                    msg = message.reference.cached_message
                    if msg==None:
                        msg = await message.channel.fetch_message(message.reference.message_id)

                    msg.content = msg.content.replace('\n','\n>')
                    if not msg.webhook_id==None:
                        author = f'@{msg.author.name}'
                        identifier_resp = author.split('(')
                        identifier_resp = identifier_resp[len(identifier_resp)-1]
                        author = author[:-(2+len(identifier_resp))]
                    else:
                        author = f'{msg.author.name}#{msg.author.discriminator}'
                        if msg.author.discriminator=='0':
                            author = f'@{msg.author.name}'
                    content = msg.content
                    if len(msg.content)==0:
                        content = '[no content]'
                    embed = discord.Embed(title=f'Replying to {author}',description=content)
                    if not msg.author.avatar==None:
                        embed.set_author(name=author,icon_url=msg.author.avatar.url)
                    else:
                        embed.set_author(name=author)
                    if message.author.bot:
                        embeds = message.embeds
                    else:
                        embeds = []
                    embeds.append(embed)
                    await webhook.send(avatar_url=url,username=message.author.global_name+ f' ({identifier})',
                                       content=message.content,embeds=embeds,
                                       files=files,allowed_mentions=mentions)
                else:
                    if message.author.bot:
                        embeds = message.embeds
                    else:
                        embeds = []
                    await webhook.send(avatar_url=url,username=message.author.global_name+ f' ({identifier})',
                                   content=message.content,embeds=embeds,
                                   files=files,allowed_mentions=mentions)

@bot.event
async def on_message_edit(before,after):
    if before.content==after.content:
        return
    message = after
    if not message.webhook_id==None:
        # webhook msg, dont bother
        return

    if message.content.startswith('u!'):
        return await bot.process_commands(message)
    
    async with aiofiles.open(f'participants_main.txt','r',encoding='utf-8') as x:
        data = await x.read()
        data = ast.literal_eval(data)
        await x.close()

    async with aiofiles.open(f'participants_pr.txt','r',encoding='utf-8') as x:
        data2 = await x.read()
        data2 = ast.literal_eval(data2)
        await x.close()

    async with aiofiles.open(f'participants_prcomments.txt','r',encoding='utf-8') as x:
        data3 = await x.read()
        data3 = ast.literal_eval(data3)
        await x.close()

    async with aiofiles.open(f'participants_liveries.txt','r',encoding='utf-8') as x:
        data4 = await x.read()
        data4 = ast.literal_eval(data4)
        await x.close()

    if not f'{message.guild.id}' in data or message.author.id==1187093090415149056:
        return

    hooks = await message.channel.webhooks()
    found = False
    hook_ids = data.setdefault(f'{message.guild.id}', [])
    hook_ids_2 = data2.setdefault(f'{message.guild.id}', [])
    hook_ids_3 = data3.setdefault(f'{message.guild.id}', [])
    hook_ids_4 = data4.setdefault(f'{message.guild.id}', [])
    origin_room = 0
    
    for webhook in hooks:
        if webhook.id in hook_ids:
            origin_room = 0
            found = True
            break
        elif webhook.id in hook_ids_2:
            origin_room = 1
            data = data2
            found = True
            break
        elif webhook.id in hook_ids_3:
            origin_room = 2
            data = data3
            found = True
            break
        elif webhook.id in hook_ids_4:
            origin_room = 3
            data = data4
            found = True
            break

    if not found:
        return

    user_hash = encrypt_string(f'{message.author.id}')[:3]
    guild_hash = encrypt_string(f'{message.guild.id}')[:3]
    identifier = user_hash + guild_hash

    for key in data:
        if int(key)==message.guild.id:
            continue
        try:
            async with aiofiles.open(f'{key}_bans.txt','r',encoding='utf-8') as x:
                banlist = await x.read()
                banlist = ast.literal_eval(banlist)
                await x.close()
        except:
            banlist = []
        if message.author.id in banlist:
            continue
        hook_ids = data.setdefault(key, [])
        sent = False
        guild = bot.get_guild(int(key))
        try:
            hooks = await guild.webhooks()
        except:
            continue
        for webhook in hooks:
            if webhook.id in hook_ids:
                try:
                    url = message.author.avatar.url
                except:
                    url = None
                files = []
                index = 0
                for attachment in message.attachments:
                    if (not 'audio' in attachment.content_type and not 'video' in attachment.content_type and
                        not 'image' in attachment.content_type):
                        continue
                    file = await attachment.to_file(use_cached=True,spoiler=attachment.is_spoiler())
                    files.append(file)
                    index += 1
                if message.author.bot:
                    embeds = message.embeds
                else:
                    embeds = []
                await webhook.send(avatar_url=url,username=message.author.global_name+ f' ({identifier})',
                                   content='> **Edited message**\n'+message.content,embeds=embeds,
                                   files=files,allowed_mentions=mentions)

bot.run('token')
