const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);
const path = require('path');
const commandLineArgs = require('command-line-args');
const nodemailer = require('nodemailer');
const fs = require('fs').promises;
// Configura il path di ADB in base al tuo sistema
// Modifica questo path con il percorso corretto di adb sul tuo sistema
const ADB_PATH = '/Users/igor/Library/Android/sdk/platform-tools/adb';  // macOS/Linux


function getRandomCoordinates() {
    const x = Math.floor(Math.random() * (1000 - 780 + 1)) + 780;
    const y = Math.floor(Math.random() * (1175 - 900 + 1)) + 900;
    return { x, y };
}

async function tapRandom() {
    const { x, y } = getRandomCoordinates();
    await execPromise(`"${ADB_PATH}" shell input tap ${x} ${y}`);
}

function getRandomNumber() {
    return Math.floor(Math.random() * (1500 - 600 + 1)) + 600;
}

async function runAdbCommands() {
    try {
        
        // Verifica che ADB sia accessibile
        console.log('Verifico ADB...');
        try {
            await execPromise(`"${ADB_PATH}" devices`);
        } catch (error) {
            throw new Error(`ADB non trovato nel path: ${ADB_PATH}. \nVerifica il percorso corretto di ADB nel tuo sistema.`);
        }
        
        await execPromise(`"${ADB_PATH}" shell input tap 410 395`);
        await new Promise(resolve => setTimeout(resolve, getRandomNumber()));



        async function executeTaps() {
            const numbers = Array.from({ length: 100 }, (_, i) => i + 1);
        
            for (const num of numbers) {
                await tapRandom();
                await new Promise(resolve => setTimeout(resolve, getRandomNumber()));
            }
        }
        
        executeTaps();


    } catch (error) {
        console.error('Errore durante l\'esecuzione:', error.message);
    }
}

// Esegui lo script
runAdbCommands();