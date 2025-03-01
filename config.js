const config = {
    marathonebet: {
        user: 'mammuthone744',
        pass: '89sumellU!!',
        package_name: 'it.marathonbet.sportsbook'
    },
    bet365: {
        user: 'mammuthone',
        pass: '89sumellU!!',
        package_name: ''
    },
    sisal: {
        user: 'autopsia',
        pass: '89sumellU!!',
        package_name: 'com.mobenga.sisal'
    },
    unibet: {
        user: 'igorbetting@outlook.it',
        pass: 'MV2CqReq.G!wPJX',
        package_name: 'com.unibet.unibetpro'
    },
};

// Esporta la configurazione
module.exports = config;

// Puoi anche esportare singoli elementi
module.exports.marathonebet = config.marathonebet;

// Funzioni helper opzionali
module.exports.getBookmaker = (name) => config[name];