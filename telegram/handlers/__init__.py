def __init__(self, bot, database):
    self.bot = bot
    self.database = database

    self.games = GamesSystem(database)
    self.developer = DeveloperSystem(database)
    self.group_os = GroupOS(bot, database)

    self.group = GroupHandler(
        bot,
        database,
        self.group_os
    )

    self.file_states = {}
    self.terminal_dirs = {}
    self.command_history = {}