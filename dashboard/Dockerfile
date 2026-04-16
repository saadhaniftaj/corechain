FROM nginx:alpine

# Copy our custom nginx config over default
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy all dashboard assets (HTML, JS, CSS)
COPY . /var/www/html/

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
