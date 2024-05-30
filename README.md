# NodePay
An unofficial Docker Image for [app.nodepay.ai](https://app.nodepay.ai/register?ref=3iXL7IuXXwKQVE6)
Available on [Docker Hub](https://hub.docker.com/r/camislav/grass)

## What's NodePay?
NodePay allows you to earn passive income by sharing your network bandwidth

## How to get started?
1. Register a Nodepay Account if you don't have one already: [app.nodepay.ai](https://app.nodepay.ai/register?ref=3iXL7IuXXwKQVE6)
2. Either build this image from source, or download it from Docker Hub
3. Set envriomental variables to their respective values: NODEPAY_USER and NODEPAY_PASS
4. You're good to go! Once started, the docker exposes your current network status and lifetime earnings on port 80

### Docker Run Command
```
docker run -d \
    --name nodepay \
    -p 8080:80 \
    -e NODEPAY_USER=myuser@mail.com \
    -e NODEPAY_PASS=mypass \
    -e ALLOW_DEBUG=False \
    double2trouble/nodepay:latest
```

Please replace 8080 with the port you want to be able to access the status with, as well as NODEPAY_USER and NODEPAY_PASS

## Separate thanks
I would like to mention [kgregor98](https://github.com/kgregor98/grass) and his project Grass for inspiring me to create this.


## License
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.


