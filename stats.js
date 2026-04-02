// stats.js

// WhatsApp Bot Stats Command

const { MessageType } = require('@adiwajshing/baileys');

// Function to send stats
const sendStats = async (client, chatId) => {
    try {
        const serverStats = await getServerStats(); // Fetch server stats from an API or database
        const responseMessage = generateStatsMessage(serverStats);

        // Send message with enhanced formatting
        await client.sendMessage(chatId, responseMessage, MessageType.text);
    } catch (error) {
        console.error('Error fetching stats:', error);
        // Send user-friendly error message
        await client.sendMessage(chatId, 'Sorry, I encountered an error while fetching the stats. Please try again later.', MessageType.text);
    }
};

// Function to generate stats message with formatting
const generateStatsMessage = (stats) => {
    return `*WhatsApp Bot Stats*

*Total Users:* ${stats.totalUsers}
*Active Sessions:* ${stats.activeSessions}
*Server Uptime:* ${formatUptime(stats.uptime)}

*Last Updated:* ${new Date().toUTCString()}`;
};

// Function to format uptime
const formatUptime = (uptime) => {
    const seconds = parseInt(uptime, 10);
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const response = [];
    if (hours) response.push(`${hours} hour${hours > 1 ? 's' : ''}`);
    if (minutes) response.push(`${minutes} minute${minutes > 1 ? 's' : ''}`);
    return response.join(' and ');
};

// Simulate fetching server stats (mock function)
const getServerStats = async () => {
    return {
        totalUsers: 150,
        activeSessions: 75,
        uptime: 3600 // in seconds
    };
};

module.exports = { sendStats };