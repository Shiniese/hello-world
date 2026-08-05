rm public/ -rf
hugo
cp robots.txt public/
wrangler pages deploy public