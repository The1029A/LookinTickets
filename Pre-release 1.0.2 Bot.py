------------------------------------- NOT TESTED VERSION 1.0.2 --------------------------------------

import discord
from discord.ext import commands, tasks
from discord.ui import Select, View, Button, Modal, TextInput
from discord.enums import TextStyle
from discord import app_commands
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.dm_messages = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)
        self.ticket_stats = {}

    async def setup_hook(self):
        await self.tree.sync()
        self.stats_task.start()
        self.archive_task.start()

bot = MyBot()

ticket_log_channel_id = None  # Provided log channel ID
ticket_category_id = None  # Provided category ID for ticket creation
support_role_id = None  # Provided support role ID
transcript_channel_id = None  # Replace with your transcript channel ID

inactive_timeout = timedelta(hours=2)
tickets = {}  # To keep track of ticket activity

priority_emojis = {
    "Low": "🟢",
    "Medium": "🟡",
    "High": "🔴"
}

allowed_purge_roles = []  # if you would like to add more than one it should look like allowed_purge_roles = [numb, numb]

embed_color = discord.Color.blue()  # Default embed color

class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="General Inquiry", emoji="💬", description="Ask a general question"),  # default title, emoji, and description
            discord.SelectOption(label="Partnership Request", emoji="🤝", description="Request a partnership"), # default title, emoji, and description
            discord.SelectOption(label="Internal Affairs", emoji="🏢", description="Report an internal issue"), # default title, emoji, and description
            discord.SelectOption(label="Application Issues", emoji="📝", description="Report an application problem"), # default title, emoji, and description
            discord.SelectOption(label="Feedback", emoji="📢", description="Provide feedback or suggestions") # default title, emoji, and description
        ]
        super().__init__(placeholder="Choose your ticket type...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        messages = {
            "General Inquiry": "REPLACE_TEXT", # This message will appear when someone opens a ticket for this certain category
            "Partnership Request": "REPLACE_TEXT", # This message will appear when someone opens a ticket for this certain category
            "Internal Affairs": "REPLACE_TEXT", # This message will appear when someone opens a ticket for this certain category
            "Application Issues": "REPLACE_TEXT", # This message will appear when someone opens a ticket for this certain category
            "Feedback": "REPLACE_TEXT" # This message will appear when someone opens a ticket for this certain category
        }

        embed = discord.Embed(title=f'{self.values[0]} Ticket', description='Please describe your issue.', color=embed_color)
        category = discord.utils.get(interaction.guild.categories, id=ticket_category_id)
        ticket_channel = await interaction.guild.create_text_channel(f'{interaction.user.name}-ticket', category=category)
        await ticket_channel.send(embed=embed)
        await ticket_channel.send(messages[self.values[0]], view=TicketView())
        await interaction.response.send_message(f'Ticket created: {ticket_channel.mention}', ephemeral=True)

        log_channel = bot.get_channel(ticket_log_channel_id)
        await log_channel.send(f'New {self.values[0]} ticket created: {ticket_channel.mention}')

        tickets[ticket_channel.id] = {"user": interaction.user, "last_activity": datetime.utcnow()}

        try:
            await interaction.user.send("A ticket has been opened.") # This is the message that will be sent to the user when a ticket is opened. You can scroll up and change True to False if you don't want the bot doing this.
        except discord.Forbidden:
            await log_channel.send(f"Could not send DM to {interaction.user.mention}.")

class TicketDropdownView(View):
    def __init__(self):
        super().__init__()
        self.add_item(TicketDropdown())

class TicketView(View):
    def __init__(self):
        super().__init__()
        self.add_item(CloseButton()) # defualt button text
        self.add_item(ClaimButton()) # defualt button text
        self.add_item(PriorityButton()) # defualt button text
        self.add_item(FeedbackButton()) # defualt button text

class CloseButton(Button):
    def __init__(self):
        super().__init__(label="Close Ticket", style=discord.ButtonStyle.red, emoji="🔒")

    async def callback(self, interaction: discord.Interaction):
        try:
            transcript_channel = bot.get_channel(transcript_channel_id)
            if transcript_channel is not None:
                await transcript_channel.send(f'Ticket closed by {interaction.user.mention} in {interaction.channel.mention}')

            try:
                await interaction.user.send(f'The ticket you opened has been closed by {interaction.user.mention}.')
            except discord.Forbidden:
                if transcript_channel is not None:
                    await transcript_channel.send(f"Could not send DM to {interaction.user.mention}.")

            del tickets[interaction.channel.id]
            await interaction.channel.delete()

        except KeyError:
            await interaction.response.send_message("Ticket not found.", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"Failed to close ticket: {e}", ephemeral=True)

class ClaimButton(Button):
    def __init__(self):
        super().__init__(label="Claim Ticket", style=discord.ButtonStyle.green, emoji="✋")

    async def callback(self, interaction: discord.Interaction):
        support_role = discord.utils.get(interaction.guild.roles, id=support_role_id)
        if support_role in interaction.user.roles:
            await interaction.channel.send(f'Ticket claimed by {interaction.user.mention}')
            self.disabled = True
            await interaction.message.edit(view=self.view)
        else:
            await interaction.response.send_message('You do not have permission to claim tickets.', ephemeral=True)

class PriorityButton(Button):
    def __init__(self):
        super().__init__(label="Set Priority", style=discord.ButtonStyle.blurple, emoji="⭐")

    async def callback(self, interaction: discord.Interaction):
        support_role = discord.utils.get(interaction.guild.roles, id=support_role_id)
        if support_role in interaction.user.roles:
            await interaction.response.send_message(content="Select a priority level:", view=PriorityView(), ephemeral=True)
        else:
            await interaction.response.send_message('You do not have permission to set priority.', ephemeral=True)

class PriorityView(View):
    def __init__(self):
        super().__init__()
        self.add_item(PriorityDropdown())

class PriorityDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Low", emoji="🟢", description="Low priority"), # defualt priority 
            discord.SelectOption(label="Medium", emoji="🟡", description="Medium priority"), # defualt priority
            discord.SelectOption(label="High", emoji="🔴", description="High priority") # defualt priority
        ]
        super().__init__(placeholder="Set ticket priority...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Priority set to: {self.values[0]}")
        await interaction.channel.edit(topic=f"Priority: {self.values[0]}")

        # Add the priority emoji to the channel name
        priority_emoji = priority_emojis[self.values[0]]
        new_channel_name = f'{priority_emoji}-{interaction.channel.name}'
        await interaction.channel.edit(name=new_channel_name)

        transcript_channel = bot.get_channel(transcript_channel_id)
        if transcript_channel is not None:
            await transcript_channel.send(f'#{interaction.channel} {interaction.user.mention} set priority to {self.values[0]}.')

class FeedbackButton(Button):
    def __init__(self):
        super().__init__(label="Submit Feedback", style=discord.ButtonStyle.blurple, emoji="💬")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(FeedbackForm())

class FeedbackForm(Modal):
    def __init__(self):
        super().__init__(title="Feedback Form", custom_id="feedback_form")
        self.add_item(TextInput(label="Was your issue or inquiry solved today?", style=TextStyle.short, required=False)) # default feedback form questions
        self.add_item(TextInput(label="What do you think we could have done better?", style=TextStyle.long, required=False)) # default feedback form questions

    async def on_submit(self, interaction: discord.Interaction):
        feedback_channel = bot.get_channel(ticket_log_channel_id)
        embed = discord.Embed(title="Ticket Feedback", color=discord.Color.blue())
        embed.add_field(name="User", value=interaction.user.mention)
        embed.add_field(name="Ticket Channel", value=interaction.channel.mention)
        embed.add_field(name="Solved", value=self.children[0].value)
        embed.add_field(name="Suggestions", value=self.children[1].value)
        await feedback_channel.send(embed=embed)
        await interaction.response.send_message("Thank you for your feedback!", ephemeral=True)

@tasks.loop(weeks=1)
async def stats_task():
    transcript_channel = bot.get_channel(transcript_channel_id)
    if transcript_channel:
        for user_id, stats in bot.ticket_stats.items():
            user = bot.get_user(user_id)
            embed = discord.Embed(title=f"{user.name}'s Ticket Statistics", color=embed_color)
            embed.add_field(name="Total Tickets Opened", value=stats.get('total_opened', 0))
            embed.add_field(name="Total Tickets Claimed", value=stats.get('total_claimed', 0))
            embed.add_field(name="Total Tickets Unclaimed", value=stats.get('total_unclaimed', 0))
            await transcript_channel.send(embed=embed)

@bot.tree.command(name="stats", description="Check your support statistics")
@app_commands.checks.has_role(support_role_id)
async def stats(interaction: discord.Interaction):
    user_stats = bot.ticket_stats.get(interaction.user.id, {})
    embed = discord.Embed(title="Your Ticket Statistics", color=embed_color)
    embed.add_field(name="Total Tickets Opened", value=user_stats.get('total_opened', 0))
    embed.add_field(name="Total Tickets Claimed", value=user_stats.get('total_claimed', 0))
    embed.add_field(name="Total Tickets Unclaimed", value=user_stats.get('total_unclaimed', 0))
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="slowmode", description="Set slowmode for ticket channel")
@app_commands.checks.has_role(support_role_id)
@app_commands.describe(duration="Slowmode duration in seconds (1-5)")
async def slowmode(interaction: discord.Interaction, duration: int):
    if duration < 1 or duration > 5:
        await interaction.response.send_message("Please enter a duration between 1 and 5 seconds.", ephemeral=True)
        return
    await interaction.channel.edit(slowmode_delay=duration)
    await interaction.response.send_message(f"Slowmode set to {duration} seconds.", ephemeral=True)

@tasks.loop(minutes=10)
async def archive_task():
    now = datetime.utcnow()
    for channel_id, info in tickets.items():
        if 'archiving_warning_sent' not in info:
            if now - info['last_activity'] > timedelta(days=4):
                transcript_channel = bot.get_channel(transcript_channel_id)
                if transcript_channel:
                    embed = discord.Embed(title="Ticket Archiving Soon! ⚠️", color=embed_color)
                    embed.add_field(name="User", value=info['user'].mention)
                    embed.add_field(name="Category", value=channel_id.split('-')[0])
                    embed.add_field(name="Ticket", value=f"<#{channel_id}>")
                    await transcript_channel.send(embed=embed)
                    info['archiving_warning_sent'] = True
        elif now - info['last_activity'] > timedelta(days=5):
            channel = bot.get_channel(channel_id)
            if channel:
                await channel.delete()
            del tickets[channel_id]

@bot.tree.command(name="info", description="Get user information")
@app_commands.checks.has_role(support_role_id)  # Ensure only the support role can use this command
@app_commands.describe(user="The user to get information for")
async def info(interaction: discord.Interaction, user: discord.User):
    join_date = user.created_at
    user_stats = bot.ticket_stats.get(user.id, {})
    embed = discord.Embed(title=f"{user.name}'s Information", color=embed_color)
    embed.add_field(name="Join Date to Discord", value=join_date.strftime("%Y-%m-%d"))
    embed.add_field(name="Total Tickets Opened", value=user_stats.get('total_opened', 0))
    embed.add_field(name="Total Tickets Claimed", value=user_stats.get('total_claimed', 0))
    embed.add_field(name="Total Tickets Unclaimed", value=user_stats.get('total_unclaimed', 0))
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="create_ticket", description="Create a new ticket")
async def create_ticket(interaction: discord.Interaction):
    embed = discord.Embed(
        title="**Select a Category**",
        description=("Create a ticket within My Server\n\n" # Default Title
                     "When creating the ticket, please choose the correct category. "  # Default description line
                     "If your category is not found, please select a general inquiry.\n"  # Default description line
                     "**Select a category to get started!**"),  # Default description line
        color=embed_color)
    await interaction.response.send_message(embed=embed, view=TicketDropdownView())

@bot.tree.command(name="notepad", description="Add a note to the current ticket") # defualt command description
@app_commands.checks.has_role(support_role_id)
@app_commands.describe(note="The note to add to the ticket") # defualt description of the command the use of notepad command can be used anywhere in the server if you dont have certain settings. Only certain roles can use this.
async def notepad(interaction: discord.Interaction, note: str):
    embed = discord.Embed(title="Staff Ticket Notes", description=note, color=discord.Color.blue()) # staff ticket notes is the title for each note they make
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Note added to the ticket.", ephemeral=True) # if you are using this for your whole server change the message if you would like

if not bot.tree.get_command("purge"):
    @bot.tree.command(name="purge", description="Purge messages in a channel")
    @app_commands.describe(amount="The number of messages to purge (1-100)")
    async def purge(interaction: discord.Interaction, amount: int):
        if amount < 1 or amount > 100:
            await interaction.response.send_message("Please enter a number between 1 and 100.", ephemeral=True) # its not recommended to go over 100
            return

        if not any(role.id in allowed_purge_roles for role in interaction.user.roles):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.channel.purge(limit=amount)
        await interaction.response.send_message(f"You successfully purged {amount} messages.", ephemeral=True)

bot.run('')
