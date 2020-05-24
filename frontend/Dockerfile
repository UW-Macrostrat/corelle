FROM node:11

WORKDIR /app/
COPY package.json /app/

RUN npm install -g parcel-bundler && npm install

COPY ./* /app/

CMD parcel build -d /app/dist --public-url './' index.html
