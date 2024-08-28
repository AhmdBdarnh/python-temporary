# Use a newer Node.js version, such as 18 or 20
FROM node:20

WORKDIR /app

# Install Serverless version 3.x globally
RUN npm install -g serverless@3

# Copy package.json and package-lock.json first to leverage Docker layer caching
COPY package*.json ./

# Install dependencies based on the package.json file
RUN npm install

# Copy the rest of your project files into the container
COPY . .

# Expose the port for serverless-offline
EXPOSE 3000

# Command to run serverless offline
CMD ["serverless", "offline"]
