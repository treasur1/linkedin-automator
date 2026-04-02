const sendErrorToOwner = (error) => {
    // Implementation to send error to owner
    console.error("An error occurred:", error);
    message.client.send(`🚨 Error: ${error.message}`);
};

module.exports = {
    top: async (message) => {
        try {
            const data = await message.client.db.query(`SELECT * FROM leaderboard ORDER BY score DESC LIMIT 10`);
            message.send(`📈 Top Players:
${data.map((player, index) => `#${index + 1} - ${player.name}: ${player.score} points`).join('\n')}`);
        } catch (error) {
            sendErrorToOwner(error);
        }
    },

    rank: async (message) => {
        try {
            const user = message.author;
            const data = await message.client.db.query(`SELECT score FROM leaderboard WHERE userId = ${user.id}`);
            if (data.length > 0) {
                message.send(`🏅 Your rank is: ${data[0].rank}`);
            } else {
                message.send(`❌ You are not ranked yet.`);
            }
        } catch (error) {
            sendErrorToOwner(error);
        }
    },

    ghosts: async (message) => {
        try {
            const data = await message.client.db.query(`SELECT * FROM ghosts WHERE userId = ${message.author.id}`);
            message.send(`👻 Your Ghosts:
${data.map(ghost => ghost.name).join(', ')}`);
        } catch (error) {
            sendErrorToOwner(error);
        }
    },

    mystats: async (message) => {
        try {
            const stats = await message.client.db.query(`SELECT * FROM userStats WHERE userId = ${message.author.id}`);
            message.send(`📊 Your Stats:
Score: ${stats.score}
Games Played: ${stats.gamesPlayed}`);
        } catch (error) {
            sendErrorToOwner(error);
        }
    }
};
