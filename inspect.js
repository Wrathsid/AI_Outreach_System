const https = require('https');
https.get('https://ai-outreach-system.vercel.app', (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    const scripts = data.match(/href=\"(\/_next\/static\/chunks\/[^\"]+)\"/g) || [];
    scripts.forEach(s => {
      const url = 'https://ai-outreach-system.vercel.app' + s.split('\"')[1];
      https.get(url, (res2) => {
        let chunkData = '';
        res2.on('data', d => chunkData += d);
        res2.on('end', () => {
          if(chunkData.includes('127.0.0.1:8000')) console.log('FOUND LOCALHOST IN', url);
          if(chunkData.includes('ai-outreach-system.onrender.com')) console.log('FOUND RENDER IN', url);
        });
      });
    });
  });
});
