 # LookinTickets Discord Bot 📝
#### A customizable discord ticket bot that keeps your support team in mind. Some key features are Automatic Inactivity Messages, Ticket Notes, Dynamic Ticket Channel Names, Purging, Feedback, and more!

### Having issues? Scroll down to the tip section to see for some solutions.

## Features 🌟
### Easy Ticket Creation 💬
Users can create tickets by selecting a category from a dropdown menu. You are able to customize each dropdown menus title and description. Also, you can change the message that appears when a user opens a ticket from each other categorys.

```ruby
class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="General Inquiry", emoji="💬", description="Ask a general question"),
            discord.SelectOption(label="Partnership Request", emoji="🤝", description="Request a partnership"),
            discord.SelectOption(label="Internal Affairs", emoji="🏢", description="Report an internal issue"),
            discord.SelectOption(label="Application Issues", emoji="📝", description="Report an application problem"),
            discord.SelectOption(label="Feedback", emoji="📢", description="Provide feedback or suggestions")
        ]
        super().__init__(placeholder="Choose your ticket type...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title=f'{self.values[0]} Ticket', description='Please describe your issue.', color=embed_color)
        category = discord.utils.get(interaction.guild.categories, id=None)
        ticket_channel = await interaction.guild.create_text_channel(f'{interaction.user.name}-ticket', category=category)
        await ticket_channel.send(embed=embed)
        await ticket_channel.send(messages[self.values[0]], view=TicketView())
        await interaction.response.send_message(f'Ticket created: {ticket_channel.mention}', ephemeral=True)
```
### Ticket Priority Levels 🟢 🟡 🔴
The role you selected will allow only certain people with the exact role to add priority levels of tickets.
```ruby
class PriorityDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Low", emoji="🟢", description="Low priority"),
            discord.SelectOption(label="Medium", emoji="🟡", description="Medium priority"),
            discord.SelectOption(label="High", emoji="🔴", description="High priority")
        ]
        super().__init__(placeholder="Set ticket priority...", min_values=1, max_values=1, options=options)
```
### Messages and inactivity Messages 💬
```ruby
class TicketDropdown(Select):
    async def callback(self, interaction: discord.Interaction):
        ticket_channel = await interaction.guild.create_text_channel(f'{interaction.user.name}-ticket', category=category)
        await ticket_channel.send(embed=embed)
        await ticket_channel.send(messages[self.values[0]], view=TicketView())
        await interaction.response.send_message(f'Ticket created: {ticket_channel.mention}', ephemeral=True)
        tickets[ticket_channel.id] = {"user": interaction.user, "last_activity": datetime.utcnow()}

        # Sending DM to user
        try:
            await interaction.user.send("A ticket has been opened.")
        except discord.Forbidden:
            log_channel = bot.get_channel(ticket_log_channel_id)
            await log_channel.send(f"Could not send DM to {interaction.user.mention}.")
            
class CloseButton(Button):
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
```
### Automatic Ticket Logs 💬
```ruby
class TicketDropdown(Select):
    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title=f'{self.values[0]} Ticket', description='Please describe your issue.', color=embed_color)
        category = discord.utils.get(interaction.guild.categories, id=None)
        ticket_channel = await interaction.guild.create_text_channel(f'{interaction.user.name}-ticket', category=category)
        await ticket_channel.send(embed=embed)
        await ticket_channel.send(messages[self.values[0]], view=TicketView())
        await interaction.response.send_message(f'Ticket created: {ticket_channel.mention}', ephemeral=True)

        # Logging the ticket creation
        log_channel = bot.get_channel(ticket_log_channel_id)
        await log_channel.send(f'New {self.values[0]} ticket created: {ticket_channel.mention}')
        tickets[ticket_channel.id] = {"user": interaction.user, "last_activity": datetime.utcnow()}

class CloseButton(Button):
    async def callback(self, interaction: discord.Interaction):
        try:
            transcript_channel = bot.get_channel(transcript_channel_id)
            if transcript_channel is not None:
                await transcript_channel.send(f'Ticket closed by {interaction.user.mention} in {interaction.channel.mention}')
            await interaction.channel.delete()
            del tickets[interaction.channel.id]

        except KeyError:
            await interaction.response.send_message("Ticket not found.", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"Failed to close ticket: {e}", ephemeral=True)
```
### Feedback System 🗯️
```ruby
class FeedbackForm(Modal):
    def __init__(self):
        super().__init__(title="Feedback Form", custom_id="feedback_form")
        self.add_item(TextInput(label="Was your issue or inquiry solved today?", style=TextStyle.short, required=False))
        self.add_item(TextInput(label="What do you think we could have done better?", style=TextStyle.long, required=False))

    async def on_submit(self, interaction: discord.Interaction):
        feedback_channel = bot.get_channel(ticket_log_channel_id)
        embed = discord.Embed(title="Ticket Feedback", color=discord.Color.blue())
        embed.add_field(name="User", value=interaction.user.mention)
        embed.add_field(name="Ticket Channel", value=interaction.channel.mention)
        embed.add_field(name="Solved", value=self.children[0].value)
        embed.add_field(name="Suggestions", value=self.children[1].value)
        await feedback_channel.send(embed=embed)
        await interaction.response.send_message("Thank you for your feedback!", ephemeral=True)
```
### Inactivity Check ✅
from datetime import datetime, timedelta
```ruby
inactive_timeout = timedelta(hours=2)
tickets = {}  # Dictionary to keep track of ticket activity

class TicketDropdown(Select):
    async def callback(self, interaction: discord.Interaction):
        ticket_channel = await interaction.guild.create_text_channel(f'{interaction.user.name}-ticket', category=category)
        tickets[ticket_channel.id] = {"user": interaction.user, "last_activity": datetime.utcnow()}
        # Rest of your code...

@tasks.loop(minutes=30)
async def check_inactive_tickets():
    now = datetime.utcnow()
    for channel_id, ticket_info in list(tickets.items()):
        if now - ticket_info["last_activity"] > inactive_timeout:
            channel = bot.get_channel(channel_id)
            if channel is not None:
                await channel.send("This ticket has been inactive for over 2 hours and will be closed.")
                await channel.delete()
                del tickets[channel_id]

# Start the loop when the bot is ready
@bot.event
async def on_ready():
    check_inactive_tickets.start()
    print(f'Logged in as {bot.user}')

# Update the last activity time whenever a message is sent in a ticket channel
@bot.event
async def on_message(message):
    if message.channel.id in tickets:
        tickets[message.channel.id]["last_activity"] = datetime.utcnow()
    await bot.process_commands(message)
```
### Purging 🚫
```ruby
if not bot.tree.get_command("purge"):
    @bot.tree.command(name="purge", description="Purge messages in a channel")
    @app_commands.describe(amount="The number of messages to purge (1-100)")
    async def purge(interaction: discord.Interaction, amount: int):
        if amount < 1 or amount > 100:
            await interaction.response.send_message("Please enter a number between 1 and 100.", ephemeral=True)
            return

        if not any(role.id in allowed_purge_roles for role in interaction.user.roles):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.channel.purge(limit=amount)
        await interaction.response.send_message(f"You successfully purged {amount} messages.", ephemeral=True)
```
### Ticket Notes 📜
```ruby
@bot.tree.command(name="notepad", description="Add a note to the current ticket")
@app_commands.checks.has_role(support_role_id)
@app_commands.describe(note="The note to add to the ticket")
async def notepad(interaction: discord.Interaction, note: str):
    embed = discord.Embed(title="Staff Ticket Notes", description=note, color=discord.Color.blue())
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Note added to the ticket.", ephemeral=True)
```
### Dynamic Ticket Channel Names 🏷️
```ruby
class TicketDropdown(Select):
    async def callback(self, interaction: discord.Interaction):
        ticket_channel = await interaction.guild.create_text_channel(f'{interaction.user.name}-ticket', category=category)

class PriorityDropdown(Select):
    async def callback(self, interaction: discord.Interaction):
        new_channel_name = f'{priority_emoji}-{interaction.channel.name}'
        await interaction.channel.edit(name=new_channel_name)
```
### Customizable Embed Colors 🎨
The embed colors should be customizable using by providing a HEX color. You can also customize the color by using the /set_color command in your server.

```ruby
@bot.tree.command(name="set_color", description="Set the embed color")
async def set_color(interaction: discord.Interaction, color: str):
    global embed_color
    embed_color = discord.Color(int(color, 16))
    await interaction.response.send_message(f"Embed color set to {color}")
embed_color = discord.Color.blue()  # Updated to use valid color attribute
```

### Claiming and Unclaiming Tickets ✋
Your selected role should allow only them to claim and unclaim tickets.

```ruby
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
```

> [!NOTE]
> The Discord bot requires the following to fully operate.
>**View Channels**
> **Manage Channels**
> **Send Messages**
> **Embed Links**
> **Manage Roles**
> **Manage Messages**
> **Presence Intent**
> **Server Members Intent**
> **Message Content Intent**

> [!TIP]
> ### Having issues starting up the bot? Maybe this can help...
> 1. **Release Not Downloaded** Create a file called *bot.py* using the notepad or a text editor then paste your code. Add this to your files.
> 1. **Release Downloaded** Go to your *file main -> bot.py* and then tap on the *bot.txt* paste your edited code and then reneame the file *bot.py*
> 3. **Release Not Downloaded** Create a file called *requirements.txt* using the notepad or a text editior and paste in: *discord.py* Add this to your files.
> 4. **Release Dowloaded** No action for *requirements.txt* is required.
> 5. **Important** Make sure that the following are in the startup tab:
>    *pip install -r requirements.txt* and *python... Bot.py* **Ex. python /home/container/Bot.py** **This is your directory make sure it is correct**
