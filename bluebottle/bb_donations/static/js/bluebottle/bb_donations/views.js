App.DonationView = App.FormView.extend({
    amount: gettext('Amount'),

  keyDown: function(e){
      var input = this.$().find('.donation-input'),
        inputVal = input.val();
      
      if (inputVal.length > 4) {
        $(input).addClass('is-long');
      } else if (inputVal.length <= 4) {
        $(input).removeClass('is-long');
      }
    } 
});

App.DonationSuccessView = Em.View.extend({
    templateName: 'donation_success',
    supported: true,

    didInsertElement: function() {
        if(!document.createElement('svg').getAttributeNS) {
            this.setProperties({
                supported: false
            });
        }
    }
});

App.CanvasView = Em.View.extend({
    tagName: 'canvas',
    elementId: 'confetti-canvas',
    mp: 350,
    angle: 0,
    colors: [[255,97,154], [0,192,81], [183,183,183]],

    didInsertElement: function() {
        var canvas = this.$(),
            ctx = canvas[0].getContext("2d"),
            W = ctx.canvas.clientWidth,
            H = ctx.canvas.clientHeight,
            particles = [], _this = this;

        $(canvas).attr('width', W)
        $(canvas).attr('height', H)
        
        for(var i = 0; i < this.mp; i++) {
            var particleColor = this.colors[~~this.range(0,3)];

            particles.push({
                x: Math.random() * W,
                y: Math.random() * H,
                r: Math.random() * 4 + 1,
                d: Math.random() * this.mp,
                color: "rgba(" + particleColor[0] + ", " + particleColor[1] + ", " + particleColor[2] + ", 0.8)"
            });
        }
        
        setInterval(function(){
            _this.draw(ctx, W, H, particles);
        }, 33);

    },

    draw: function(ctx, width, height, currentParticles) {
        ctx.clearRect(0, 0, width, height);
            
        for (var i = 0; i < this.mp; i++) { 
            var p = currentParticles[i];
            ctx.beginPath();
            ctx.fillStyle = p.color;
            ctx.moveTo(p.x, p.y);
            ctx.arc(p.x, p.y, p.r, 0, Math.PI*2, true);
            ctx.fill();
        }

        this.update(width, height, currentParticles);
    },

    update: function(width, height, currentParticles) {
        this.angle += 0.01;

        for (var i = 0; i < this.mp; i++) {
            var p = currentParticles[i];
            //Updating X and Y coordinates
            //We will add 1 to the cos function to prevent negative values which will lead flakes to move upwards
            //Every particle has its own density which can be used to make the downward movement different for each flake
            //Lets make it more random by adding in the radius
            p.y += Math.cos(this.angle + p.d) + 1 + p.r/2;
            p.x += Math.sin(this.angle) * 2;
            
            //Sending flakes back from the top when it exits
            //Lets make it a bit more organic and let flakes enter from the left and right also.
            if(p.x > width + 5 || p.x < - 5 || p.y > height) {
                if(i % 3 > 0) { //66.67% of the flakes
                    currentParticles[i] = {x: Math.random() * width, y: -10, r: p.r, d: p.d, color : p.color};
                } else {
                    //If the flake is exitting from the right
                    if(Math.sin(this.angle) > 0) {
                        //Enter from the left
                        currentParticles[i] = {x: - 5, y: Math.random() * height, r: p.r, d: p.d, color: p.color};
                    } else {
                        //Enter from the right
                        currentParticles[i] = {x: width + 5, y: Math.random() * height, r: p.r, d: p.d, color : p.color};
                    }
                }
            }
        }
    },

    range: function(a, b) {
        return (b - a) * Math.random() + a;
    }
});


