Ember.TEMPLATES['_my_project_top'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                <em class=\"account-subtitle\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</em>\n			");
  return buffer;
  }

function program3(depth0,data) {
  
  
  data.buffer.push("\n			    <em class=\"account-subtitle\">Projects</em>\n			");
  }

function program5(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.unless.call(depth0, "isPhasePitch", {hash:{},inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n        ");
  return buffer;
  }
function program6(depth0,data) {
  
  
  data.buffer.push("\n        <a class=\"account-preview btn-link\">\n            <span class=\"flaticon solid eye-1\"></span>\n            View project\n        </a>\n        ");
  }

function program8(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n            <ul class=\"tabs steps five\">\n                <li>\n                    <a>\n                        <span class=\"tab-icon\"><span class=\"flaticon solid lightbulb-3\"></span></span>\n                        <strong class=\"tab-title\">\n                            Pitch\n                            <em class=\"tab-subtitle\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "pitch.status", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("&nbsp;</em>\n                        </strong>\n                    </a>\n                </li>\n                <li>\n                    <span>\n                        <span class=\"tab-icon\"><span class=\"flaticon solid notebook-1\"></span></span>\n                        <strong class=\"tab-title\">\n                            Plan\n                            <em class=\"tab-subtitle\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "plan.status", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("&nbsp;</em>\n                        </strong>\n                    </span>\n                </li>\n                <li>\n                    <span>\n                        <span class=\"tab-icon\"><span class=\"flaticon solid wallet-1\"></span></span>\n                        <strong class=\"tab-title\">\n                            Campaign\n                            <em class=\"tab-subtitle\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "campaign.status", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("&nbsp;</em>\n                        </strong>\n                    </span>\n                </li>\n                <li>\n                    <span>\n                        <span class=\"tab-icon\"><span class=\"flaticon solid wrench-1\"></span></span>\n                        <strong class=\"tab-title\">Execute\n                            <em class=\"tab-subtitle\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "act.status", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("&nbsp;</em>\n                        </strong>\n                    </span>\n                </li>\n                <li>\n                    <span>\n                        <span class=\"tab-icon\"><span class=\"flaticon solid flag-3\"></span></span>\n                        <strong class=\"tab-title\">Results\n                            <em class=\"tab-subtitle\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "results.status", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("&nbsp;</em>\n                        </strong>\n                    </span>\n                </li>\n            </ul>\n        ");
  return buffer;
  }

  data.buffer.push("<div class=\"l-section account-header\">\n    <nav class=\"l-wrapper\">    \n    \n        <figure class=\"account-avatar\"><img ");
  hashContexts = {'src': depth0};
  hashTypes = {'src': "STRING"};
  data.buffer.push(escapeExpression(helpers.bindAttr.call(depth0, {hash:{
    'src': ("controllers.currentUser.getAvatar")
  },contexts:[],types:[],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("  /></figure>\n        \n        <header class=\"account-title\">\n            <h2>My 1% \n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "title", {hash:{},inverse:self.program(3, program3, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </h2>\n        </header>\n                 \n        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "title", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n        \n        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "id", {hash:{},inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    </nav>\n</div>");
  return buffer;
  
});Ember.TEMPLATES['_signup_content'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  
  data.buffer.push("\n	<div class=\"signup-succes\">\n    	<h2>Thanks for signing up!</h2>\n		<p>We've sent you an email. Please click <strong>Activate Profile</strong> in the email we just sent you.</p>\n	</div>\n");
  }

function program3(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n    <form>\n    	<fieldset>\n            <div class=\"control-group\">\n                <label class=\"control-label\">\n                    Name\n                </label>\n\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'class': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'class': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("first_name"),
    'placeholder': ("First name"),
    'class': ("inline-prepend"),
    'classBinding': ("errors.first_name.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'class': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'class': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("last_name"),
    'placeholder': ("Surname"),
    'class': ("inline-append"),
    'classBinding': ("errors.last_name.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n            </div>\n\n            <div class=\"control-group\">\n                <label class=\"control-label\">\n                    Email\n                </label>\n\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'type': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'type': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("email"),
    'type': ("email"),
    'classBinding': ("errors.email.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.email", {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </div>\n\n            <div class=\"control-group\">\n                <label class=\"control-label\">\n                    Password\n                </label>\n\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'type': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'type': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("password"),
    'type': ("password"),
    'classBinding': ("errors.password.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.password", {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </div>\n    	</fieldset>\n    	\n        <div class=\"signup-agree\">\n            By joining 1%Club I hereby agree to the \n            <a>1%Club Terms of service</a>\n       </div>\n       \n        <button class=\"btn btn-iconed btn-primary\">\n            <em class=\"flaticon solid user-1\"></em>\n            Sign up\n        </button>\n    </form>\n");
  return buffer;
  }
function program4(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.email", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }
function program5(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program7(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.password", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }

  data.buffer.push("<header class=\"page-header\">\n	<h1>Join 1%Club</h1>\n	<p> 1%Club is the global platform where you can share a little and change the world, in your vary own way. We ignite modern society to share 1% and support smart ideas from people in developing countries. We do this in a new, open way, believing in the power of collaboration boosted by today's technical possibilities. If we all share a little, we can change the world.</p>\n</header>\n    \n");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isUserCreated", {hash:{},inverse:self.program(3, program3, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  return buffer;
  
});Ember.TEMPLATES['_signup_sidebar'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', hashTypes, hashContexts, escapeExpression=this.escapeExpression;


  data.buffer.push("<div class=\"login-link\">\n    <a ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.action.call(depth0, "openInBox", "login", {hash:{},contexts:[depth0,depth0],types:["ID","STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(">\n    	<em class=\"flaticon solid unlock-3\"></em>\n        <strong>Already have an account?</strong><br>\n        Log in here, fast & easy\n    </a>\n</div>\n\n<div class=\"signup-advantage\">\n    <em class=\"flaticon solid heart-1\"></em>\n	<h3>Why join 1%Club?</h3>\n    <ol>\n        <li>It's easy to find projects you like.</li>\n        <li>A fun and personal way to share your 1%.</li>\n        <li>You'll receive updates on the progress of the projects you support.</li>\n    </ol>\n</div>");
  return buffer;
  
});Ember.TEMPLATES['_thanksDonation'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, escapeExpression=this.escapeExpression, self=this, helperMissing=helpers.helperMissing;

function program1(depth0,data) {
  
  var buffer = '', hashContexts, hashTypes;
  data.buffer.push("\n            <figure class=\"project-image\">\n                <img ");
  hashContexts = {'src': depth0,'alt': depth0};
  hashTypes = {'src': "STRING",'alt': "STRING"};
  data.buffer.push(escapeExpression(helpers.bindAttr.call(depth0, {hash:{
    'src': ("donation.project.plan.image.square"),
    'alt': ("project.title")
  },contexts:[],types:[],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("  />\n            </figure>\n            <h2>\n                ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "donation.project.title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                <em class=\"project-location\">\n                    <span class=\"flaticon solid location-pin-1\"></span> ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "donation.project.plan.country.name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </em>\n            </h2>\n        ");
  return buffer;
  }

  data.buffer.push("<li class=\"project-item\">\n        ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "project", "donation.project", options) : helperMissing.call(depth0, "linkTo", "project", "donation.project", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n\n        <p class=\"fund-amount\">\n            <span class=\"fund-amount-needed\">\n                <strong>&euro; ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "donation.project.campaign.money_needed", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong>\n                still needed\n            </span>\n        </p>\n    </li>");
  return buffer;
  
});Ember.TEMPLATES['contact_message'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  
  data.buffer.push("\n		                	<legend>\n								<strong>Thanks for your message!. We'll get back to you soon.</strong>\n							</legend>\n		                ");
  }

function program3(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n		                    <fieldset>\n		                        <ul>\n		                            <li class=\"control-group\">\n		                                <label class=\"control-label\">Name</label>\n		                                <div class=\"controls\">\n		                                    ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("name"),
    'classBinding': ("errors.name.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n		                                </div>\n		\n		                                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.name", {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n		                            </li>\n		\n		                            <li class=\"control-group\">\n		                                <label class=\"control-label\">Email</label>\n		                                <div class=\"controls\">\n		                                    ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("email"),
    'classBinding': ("errors.email.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n		                                </div>\n		\n		                                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.email", {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n		\n		                            </li>\n		\n		                            <li class=\"control-group\">\n		                                <label class=\"control-label\">Message</label>\n		                                <div class=\"controls\">\n		                                    ");
  hashContexts = {'valueBinding': depth0,'rows': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'rows': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextArea", {hash:{
    'valueBinding': ("message"),
    'rows': ("6"),
    'classBinding': ("errors.message.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n		                                </div>\n		\n		                                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.message", {hash:{},inverse:self.noop,fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n		\n		                            </li>\n		\n		                        </ul>\n		                    </fieldset>\n		                    <button><span class=\"flaticon solid envelope-1\"></span>Send Message</button>\n		                ");
  return buffer;
  }
function program4(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n		                                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.name", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n		                                ");
  return buffer;
  }
function program5(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program7(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n		                                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.email", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n		                                ");
  return buffer;
  }

function program9(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n		                                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.message", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n		                                ");
  return buffer;
  }

  data.buffer.push("<div class=\"l-section\" id=\"page\">\n        <section class=\"l-wrapper\">\n        \n            	<article class=\"l-content\">\n                    <header class=\"page-header\">\n                        <h1>Contact</h1>\n                        <p>\n                            \n                            Send us a message or get in touch using the details below. Talk to you soon!\n                            \n                        </p>\n                    </header>\n					\n		            <form id=\"contact-form\">\n		                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isSent", {hash:{},inverse:self.program(3, program3, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n		            </form>\n            	</article>\n            	\n	            <sidebar class=\"l-sidebar\">\n	            	<h3>Other ways to contact</h3>\n\n<p>\n    Email:<a href=\"mailto:info@onepercentclub.com?subject=Contact\">info@onepercentclub.com</a><br>\n    Twitter:<a href=\"https://twitter.com/1percentclub\">@1percentclub</a><br>\n    Facebook: <a href=\"http://www.facebook.com/onepercentclub\">/onepercentclub</a>\n</p>\n<p>\n    1%Club Foundation<br>\n    's Gravenhekje 1a<br>\n    1011 TG Amsterdam<br>\n    The Netherlands<br>\n</p>\n<p>\n    Bank: Rabobank (Haarlem)<br>\n    Account number: NL45 RABO 01322070 44(donations)<br>\n    BIC: RABONL2U<br>\n    <br>\n    Chamber of Commerce number 34.26.78.95<br>\n    Phone(+31) 20 715 8980<br>\n</p>\n\n	            </sidebar>\n	            \n        </section>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['currentOrder'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, self=this, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression;

function program1(depth0,data) {
  
  var buffer = '', stack1, stack2, hashContexts, hashTypes, options;
  data.buffer.push("\n        <div class=\"l-section\">\n            <section class=\"l-wrapper\">\n                <div class=\"l-content\">\n                    <header>\n                        <h1>Order digital 1%GIFTCARDS</h1>\n                    </header>\n                </div>\n                <sidebar class=\"l-sidebar\">\n                    ");
  hashContexts = {'tagName': depth0,'class': depth0};
  hashTypes = {'tagName': "STRING",'class': "STRING"};
  options = {hash:{
    'tagName': ("a"),
    'class': ("btn-link")
  },inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "currentOrder.donationList", options) : helperMissing.call(depth0, "linkTo", "currentOrder.donationList", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                </sidebar>\n            </section>\n        </div>\n    ");
  return buffer;
  }
function program2(depth0,data) {
  
  
  data.buffer.push("\n                        <span class=\"flaticon solid credit-card-1\"></span> Switch to donations\n                    ");
  }

function program4(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n        <div class=\"l-section fund-header\">\n            <section class=\"l-wrapper\">\n            \n                <header class=\"l-header\">\n                    <h1>Support one or more projects!</h1>\n                \n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "controllers.currentUser.isAuthenticated", {hash:{},inverse:self.program(7, program7, data),fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                \n	                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "controller.isVoucherOrder", {hash:{},inverse:self.program(11, program11, data),fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	\n	                ");
  hashContexts = {'classNames': depth0};
  hashTypes = {'classNames': "STRING"};
  stack1 = helpers.view.call(depth0, "App.OrderNavView", {hash:{
    'classNames': ("details")
  },inverse:self.noop,fn:self.program(15, program15, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                \n					");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.unless.call(depth0, "controllers.currentUser.isAuthenticated", {hash:{},inverse:self.noop,fn:self.program(18, program18, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n	                ");
  hashContexts = {'classNames': depth0};
  hashTypes = {'classNames': "STRING"};
  stack1 = helpers.view.call(depth0, "App.OrderNavView", {hash:{
    'classNames': ("payment")
  },inverse:self.noop,fn:self.program(22, program22, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </ul>\n				</header>\n                \n                \n            </section>\n        </div>\n    ");
  return buffer;
  }
function program5(depth0,data) {
  
  
  data.buffer.push("\n                	<ul class=\"tabs steps three\">\n                    ");
  }

function program7(depth0,data) {
  
  
  data.buffer.push("\n                	<ul class=\"tabs steps four\">\n                    ");
  }

function program9(depth0,data) {
  
  
  data.buffer.push("\n	                    \n	                ");
  }

function program11(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n	                    ");
  hashContexts = {'classNames': depth0};
  hashTypes = {'classNames': "STRING"};
  stack1 = helpers.view.call(depth0, "App.OrderNavView", {hash:{
    'classNames': ("support")
  },inverse:self.noop,fn:self.program(12, program12, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                ");
  return buffer;
  }
function program12(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n	                        ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(13, program13, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "currentOrder.donationList", options) : helperMissing.call(depth0, "linkTo", "currentOrder.donationList", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n	                    ");
  return buffer;
  }
function program13(depth0,data) {
  
  
  data.buffer.push("<span class=\"flaticon solid menu-list-4\"></span> Projects");
  }

function program15(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n	                    ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(16, program16, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "paymentProfile", options) : helperMissing.call(depth0, "linkTo", "paymentProfile", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n	                ");
  return buffer;
  }
function program16(depth0,data) {
  
  
  data.buffer.push("<span class=\"flaticon solid mail-3\"></span> Details");
  }

function program18(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n	                	");
  hashContexts = {'classNames': depth0};
  hashTypes = {'classNames': "STRING"};
  stack1 = helpers.view.call(depth0, "App.OrderNavView", {hash:{
    'classNames': ("profile")
  },inverse:self.noop,fn:self.program(19, program19, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n					");
  return buffer;
  }
function program19(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n	                   		");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(20, program20, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "paymentSignup", options) : helperMissing.call(depth0, "linkTo", "paymentSignup", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n					   	");
  return buffer;
  }
function program20(depth0,data) {
  
  
  data.buffer.push("<span class=\"flaticon solid user-1\"></span> Profile");
  }

function program22(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n	                    ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(23, program23, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "paymentSelect", options) : helperMissing.call(depth0, "linkTo", "paymentSelect", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n	                ");
  return buffer;
  }
function program23(depth0,data) {
  
  
  data.buffer.push("<span class=\"flaticon solid wallet-1\"></span> Payment");
  }

function program25(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                <div>\n                    <a>&times;</a>\n\n                    <div class=\"message-content\">\n                        ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "message_content", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    </div>\n                </div>\n            ");
  return buffer;
  }

  data.buffer.push("<div id=\"fund\">\n    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "controller.isVoucherOrder", {hash:{},inverse:self.program(4, program4, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n    <div class=\"l-section\">\n        <section class=\"l-wrapper\">\n\n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "display_message", {hash:{},inverse:self.noop,fn:self.program(25, program25, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n            ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "outlet", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n\n        </section>\n    </div>\n</div>");
  return buffer;
  
});Ember.TEMPLATES['currentOrderDonation'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashContexts, hashTypes, options, escapeExpression=this.escapeExpression, self=this, helperMissing=helpers.helperMissing;

function program1(depth0,data) {
  
  var buffer = '', hashContexts, hashTypes;
  data.buffer.push("\n        <figure class=\"project-image\">\n            <img ");
  hashContexts = {'src': depth0,'alt': depth0};
  hashTypes = {'src': "STRING",'alt': "STRING"};
  data.buffer.push(escapeExpression(helpers.bindAttr.call(depth0, {hash:{
    'src': ("project.plan.image.square"),
    'alt': ("project.title")
  },contexts:[],types:[],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("  />\n        </figure>\n        <h2 class=\"project-title\">\n            ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n            <em class=\"project-location\">\n                <span class=\"flaticon solid location-pin-1\"></span> ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.plan.country.name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n            </em>\n        </h2>\n    ");
  return buffer;
  }

function program3(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                <span class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "error", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</span>\n            ");
  return buffer;
  }

  hashContexts = {'class': depth0};
  hashTypes = {'class': "STRING"};
  options = {hash:{
    'class': ("project-header")
  },inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "project", "project", options) : helperMissing.call(depth0, "linkTo", "project", "project", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n\n    <div class=\"fund-amount\">\n        <strong class=\"fund-amount-needed\">&euro; ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.campaign.money_needed", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong> is still needed\n        <div class=\"fund-amount-control\">\n            ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers.each.call(depth0, "error", "in", "errors.amount", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n            <label for=\"fund-amount-1\">I'd like to give</label>\n            <span class=\"currency\"><em>&euro; </em>\n                <input type=\"number\" class=\"fund-amount-input\" id=\"fund-amount-1\" step=\"5\" name=\"fund-amount-1\" size=\"8\" maxlength=\"4\">\n            </span>            \n        </div>\n    </div>\n    \n    <a><span class=\"flaticon solid x-2\"></span> <strong>Delete</strong></a>");
  return buffer;
  
});Ember.TEMPLATES['current_order_donation_list'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts, options;
  data.buffer.push("\n            ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.render || depth0.render),stack1 ? stack1.call(depth0, "currentOrderDonation", "donation", options) : helperMissing.call(depth0, "render", "currentOrderDonation", "donation", options))));
  data.buffer.push("\n        ");
  return buffer;
  }

function program3(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n        \n        	<div class=\"fund-empty\">\n            ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "projectList", options) : helperMissing.call(depth0, "linkTo", "projectList", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n        	</div>\n        ");
  return buffer;
  }
function program4(depth0,data) {
  
  
  data.buffer.push("\n                <em class=\"flaticon solid plus-2\"></em>\n                <legend>\n                    <strong>Choose a project to support</strong>\n                    <p>Choose a project and click 'Support this project' to add it to your list.</p>\n                </legend>\n            ");
  }

function program6(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("<em class=\"flaticon solid plus-2\"></em>\n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "length", {hash:{},inverse:self.program(9, program9, data),fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n        ");
  return buffer;
  }
function program7(depth0,data) {
  
  
  data.buffer.push("\n                Add another project\n            ");
  }

function program9(depth0,data) {
  
  
  data.buffer.push("\n                Add a project\n            ");
  }

function program11(depth0,data) {
  
  
  data.buffer.push("\n	        <button><span class=\"flaticon solid right-2\"></span>Next Step</button>\n	    ");
  }

function program13(depth0,data) {
  
  
  data.buffer.push("\n	        <button disabled=\"disabled\" class=\"btn btn-iconed btn-next\"><span class=\"flaticon solid right-2\"></span>Next Step</button>\n	    ");
  }

function program15(depth0,data) {
  
  
  data.buffer.push("\n		<h3>Why not donate monthly?</h3>\n		<p>You're about to support a 1%Project. Great! Did you know you can also share a little every month? How? Choose 'monthly' and become a 1%Friend!</p>\n	");
  }

function program17(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n		<h3>Did you know?</h3>\n		<p>You're about to support a 1%Project. Great! Did you know you can also share a little every month? How? By becoming a 1%Member and choosin' monthly.\n		<p class=\"btn-link\">");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(18, program18, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "signup", options) : helperMissing.call(depth0, "linkTo", "signup", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("</p>\n	");
  return buffer;
  }
function program18(depth0,data) {
  
  
  data.buffer.push("Become a 1%Member <span class=\"flaticon solid right-angle-quote-1\"></span>");
  }

  data.buffer.push("<form class=\"l-content\">\n	    \n        <ul class=\"project-list\">\n        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "donation", "in", "controller", {hash:{},inverse:self.program(3, program3, data),fn:self.program(1, program1, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n        </ul>\n        \n        <fieldset class=\"fund-total\">\n            <div class=\"fund-total-label\">Total</div>\n            <div class=\"fund-total-amount\"><em class=\"currency\">&euro;</em> ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "singleTotal", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</div>\n        </fieldset>\n\n        ");
  hashContexts = {'class': depth0};
  hashTypes = {'class': "STRING"};
  options = {hash:{
    'class': ("btn-link btn-add")
  },inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "projectList", options) : helperMissing.call(depth0, "linkTo", "projectList", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n        \n	    ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "readyForPayment", {hash:{},inverse:self.program(13, program13, data),fn:self.program(11, program11, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n	    \n	</form>\n\n<div class=\"l-sidebar\">\n	");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "controllers.currentUser.isAuthenticated", {hash:{},inverse:self.program(17, program17, data),fn:self.program(15, program15, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n</div>");
  return buffer;
  
});Ember.TEMPLATES['current_order_voucher'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', hashTypes, hashContexts, escapeExpression=this.escapeExpression;


  data.buffer.push("<div class=\"name\">\n        <h4>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "receiver_name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</h4>\n    </div>\n    <div class=\"mail\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "receiver_email", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</div>\n    <div class=\"amount right\">\n        <span class=\"right\">&euro;");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "amount", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</span>\n    </div>\n    <div class=\"actions manage-delete\"><a>Delete</a></div>");
  return buffer;
  
});Ember.TEMPLATES['current_order_voucher_list'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, escapeExpression=this.escapeExpression, self=this, helperMissing=helpers.helperMissing;

function program1(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.CurrentOrderVoucherView", {hash:{},contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n            ");
  return buffer;
  }

function program3(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                <li>\n                    <div class=\"summary\">\n                        ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "length", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" 1%GIFTCARDS will be sent out with a total value of\n                    </div>\n                    <div class=\"amount\">\n                        <h4 class=\"right\">&euro;");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "singleTotal", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</h4>\n                    </div>\n                </li>\n            ");
  return buffer;
  }

function program5(depth0,data) {
  
  
  data.buffer.push("\n                <li>\n                    <div class=\"summary\">\n                        No gift cards in shopping basket\n                    </div>\n                </li>\n            ");
  }

function program7(depth0,data) {
  
  var buffer = '', stack1, stack2, hashContexts, hashTypes, options;
  data.buffer.push("\n            ");
  hashContexts = {'class': depth0};
  hashTypes = {'class': "STRING"};
  options = {hash:{
    'class': ("btn btn-primary btn-iconed btn-next")
  },inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "paymentProfile", options) : helperMissing.call(depth0, "linkTo", "paymentProfile", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n        ");
  return buffer;
  }
function program8(depth0,data) {
  
  
  data.buffer.push("<em class=\"flaticon solid right-2\"></em>Next Step");
  }

function program10(depth0,data) {
  
  
  data.buffer.push("\n            <button disabled=\"disabled\" class=\"btn btn-iconed  btn-next\"><span class=\"flaticon solid right-2\"></span>Next Step</button>\n        ");
  }

  data.buffer.push("<fieldset>\n\n        ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.render || depth0.render),stack1 ? stack1.call(depth0, "currentOrderVoucherNew", options) : helperMissing.call(depth0, "render", "currentOrderVoucherNew", options))));
  data.buffer.push("\n\n        <ul class=\"voucher-list\">\n            ");
  hashContexts = {'itemController': depth0};
  hashTypes = {'itemController': "ID"};
  stack2 = helpers.each.call(depth0, "controller", {hash:{
    'itemController': ("currentOrderVoucher")
  },inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n\n            ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "length", {hash:{},inverse:self.program(5, program5, data),fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n        </ul>\n\n\n        ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "length", {hash:{},inverse:self.program(10, program10, data),fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n\n    </fieldset>");
  return buffer;
  
});Ember.TEMPLATES['current_order_voucher_new'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', hashContexts, hashTypes;
  data.buffer.push("\n                        ");
  hashContexts = {'value': depth0,'id': depth0};
  hashTypes = {'value': "STRING",'id': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': ("en"),
    'id': ("lang_en")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        <label for=\"lang_en\">English</label>\n\n                        ");
  hashContexts = {'value': depth0,'id': depth0};
  hashTypes = {'value': "STRING",'id': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': ("nl"),
    'id': ("lang_nl")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        <label for=\"lang_nl\">Dutch</label>\n                    ");
  return buffer;
  }

function program3(depth0,data) {
  
  var buffer = '', hashContexts, hashTypes;
  data.buffer.push("\n                        ");
  hashContexts = {'value': depth0,'id': depth0};
  hashTypes = {'value': "INTEGER",'id': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': (10),
    'id': ("amount_10")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        <label for=\"amount_10\">\n                            &euro;10\n                        </label>\n                        ");
  hashContexts = {'value': depth0,'id': depth0};
  hashTypes = {'value': "INTEGER",'id': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': (25),
    'id': ("amount_25")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        <label for=\"amount_25\">\n                            &euro;25\n                        </label>\n                        ");
  hashContexts = {'value': depth0,'id': depth0};
  hashTypes = {'value': "INTEGER",'id': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': (50),
    'id': ("amount_50")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        <label for=\"amount_50\">\n                            &euro;50\n                        </label>\n                        ");
  hashContexts = {'value': depth0,'id': depth0};
  hashTypes = {'value': "INTEGER",'id': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': (100),
    'id': ("amount_100")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        <label for=\"amount_100\">\n                            &euro;100\n                        </label>\n                    ");
  return buffer;
  }

function program5(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.sender_name", {hash:{},inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }
function program6(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program8(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.sender_email", {hash:{},inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }

function program10(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.receiver_name", {hash:{},inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }

function program12(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.receiver_email", {hash:{},inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }

function program14(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.message", {hash:{},inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }

  data.buffer.push("<div class=\"form-meta\">\n        <p class=\"form-label\">Choose value & personalize 1%GIFTCARD</p>\n    </div>\n\n    <fieldset>\n        <ul>\n            <li class=\"control-group\">\n                <label class=\"control-label\">Language</label>\n\n                <div class=\"controls\">\n                    ");
  hashContexts = {'class': depth0,'name': depth0,'selectedValueBinding': depth0};
  hashTypes = {'class': "STRING",'name': "STRING",'selectedValueBinding': "STRING"};
  stack1 = helpers.view.call(depth0, "Em.RadioButtonGroup", {hash:{
    'class': ("big-radio radio2"),
    'name': ("language"),
    'selectedValueBinding': ("language")
  },inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </div>\n            </li>\n\n            <li class=\"control-group\">\n                <label class=\"control-label\">Value</label>\n\n                <div class=\"controls\">\n                    ");
  hashContexts = {'class': depth0,'name': depth0,'selectedValueBinding': depth0};
  hashTypes = {'class': "STRING",'name': "STRING",'selectedValueBinding': "STRING"};
  stack1 = helpers.view.call(depth0, "Em.RadioButtonGroup", {hash:{
    'class': ("big-radio radio4"),
    'name': ("amount"),
    'selectedValueBinding': ("amount")
  },inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </div>\n            </li>\n\n            <li class=\"control-group\">\n                <label class=\"control-label\">Your name</label>\n\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("sender_name"),
    'classBinding': ("errors.sender_name.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.sender_name", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n\n            <li class=\"control-group\">\n                <label class=\"control-label\">Your email</label>\n\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("sender_email"),
    'classBinding': ("errors.sender_email.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.sender_email", {hash:{},inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n        </ul>\n    </fieldset>\n\n    <hr class=\"form-divider\">\n\n    <fieldset>\n        <legend><strong>This gift card is for:</strong></legend>\n\n        <ul>\n            <li class=\"control-group\">\n                <label class=\"control-label\">Name</label>\n\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("receiver_name"),
    'classBinding': ("errors.receiver_name.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.receiver_name", {hash:{},inverse:self.noop,fn:self.program(10, program10, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n\n            <li class=\"control-group\">\n                <label class=\"control-label\">Email</label>\n\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("receiver_email"),
    'classBinding': ("errors.receiver_email.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.receiver_email", {hash:{},inverse:self.noop,fn:self.program(12, program12, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n\n            <li class=\"control-group\">\n                <label class=\"control-label\">Personal message</label>\n\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextArea", {hash:{
    'valueBinding': ("message"),
    'placeholder': ("Your message that will appear on the digital voucher."),
    'classBinding': ("errors.message.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.message", {hash:{},inverse:self.noop,fn:self.program(14, program14, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n        </ul>\n    </fieldset>\n\n    <a>Add</a>\n    <br class=\"clear\">");
  return buffer;
  
});Ember.TEMPLATES['custom_voucher_request'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                                <div class=\"errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.amount", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                            ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program4(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                                <div class=\"errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.contact_name", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                            ");
  return buffer;
  }

function program6(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                                <div class=\"errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.contact_email", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                            ");
  return buffer;
  }

function program8(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                                <div class=\"errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.organization", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                            ");
  return buffer;
  }

function program10(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                                <div class=\"errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.contact_phone", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                            ");
  return buffer;
  }

  data.buffer.push("<div class=\"container section\">\n        <header class=\"wrapper\">\n            <div class=\"content\">\n                <h1 class=\"\">Contact us for 1%GIFTCARDS</h1>\n                Please send us a message and tell us your wishes and we will contact you as soon as possible. Or call us directly on (+31) 20 715 8980.\n            </div>\n        </header>\n    </div>\n    <br>\n    <div class=\"container\">\n        <section class=\"wrapper\">\n            <form>\n                <fieldset>\n                    <ul>\n\n                        <li class=\"control-group\">\n                            <label class=\"control-label\">Value of Gift Cards</label>\n                            <div class=\"controls\">\n                                ");
  hashContexts = {'valueBinding': depth0};
  hashTypes = {'valueBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("value")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                            </div>\n                            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.amount", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                        </li>\n\n                        <li class=\"control-group\">\n                            <label class=\"control-label\">Number of Gift Cards</label>\n                            <div class=\"controls\">\n                                ");
  hashContexts = {'valueBinding': depth0,'type': depth0,'step': depth0};
  hashTypes = {'valueBinding': "STRING",'type': "STRING",'step': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("number"),
    'type': ("number"),
    'step': ("10")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                            </div>\n                            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.amount", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                        </li>\n\n                        <li class=\"control-group\">\n                            <label class=\"control-label\">Your name</label>\n                            <div class=\"controls\">\n                                ");
  hashContexts = {'valueBinding': depth0};
  hashTypes = {'valueBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("contact_name")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                            </div>\n                            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.contact_name", {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                        </li>\n\n                        <li class=\"control-group\">\n                            <label class=\"control-label\">Your email</label>\n                            <div class=\"controls\">\n                                ");
  hashContexts = {'valueBinding': depth0};
  hashTypes = {'valueBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("contact_email")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                            </div>\n                            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.contact_email", {hash:{},inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                        </li>\n\n                        <li class=\"control-group\">\n                            <label class=\"control-label\">Organisation</label>\n                            <div class=\"controls\">\n                                ");
  hashContexts = {'valueBinding': depth0};
  hashTypes = {'valueBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("organization")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                            </div>\n                            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.organization", {hash:{},inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                        </li>\n\n                        <li class=\"control-group\">\n                            <label class=\"control-label\">Phone number</label>\n                            <div class=\"controls\">\n                                ");
  hashContexts = {'valueBinding': depth0};
  hashTypes = {'valueBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("contact_phone")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                            </div>\n                            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.contact_phone", {hash:{},inverse:self.noop,fn:self.program(10, program10, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                        </li>\n                        <li class=\"control-group\">\n                            Anything else you’d like to ask? Send us a message!\n                            ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextArea", {hash:{
    'valueBinding': ("message"),
    'classBinding': ("errors.message.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </li>\n                        <li class=\"control-group\">\n                            <a class=\"right button\">Send message</a>\n                        </li>\n                    </ul>\n                </fieldset>\n\n            </form>\n        </section>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['custom_voucher_request_done'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  


  data.buffer.push("<div class=\"container section\">\n\n        <header class=\"wrapper\">\n            <h1 class=\"\">Thanks for your request. We'll get back to you soon!</h1>\n            <h2 class=\"green\">YOU MAKE IT WORK!</h2>\n        </header>\n\n    </div>");
  
});Ember.TEMPLATES['home'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n            ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.HomeBannerView", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n        ");
  return buffer;
  }

function program3(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n            ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.HomeProjectView", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n        ");
  return buffer;
  }

function program5(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n            ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.HomeQuotesView", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n        ");
  return buffer;
  }

function program7(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n            ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.HomeImpactView", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n        ");
  return buffer;
  }

  data.buffer.push("<div id=\"home\">\n        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "slides", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n		\n        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "project", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n        \n        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "quote", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n		\n        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "impact", {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['home_banner'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n		        <li class=\"carousel-item\" ");
  hashContexts = {'id': depth0};
  hashTypes = {'id': "ID"};
  data.buffer.push(escapeExpression(helpers.bindAttr.call(depth0, {hash:{
    'id': ("style")
  },contexts:[],types:[],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(">\n		        	<div class=\"l-wrapper\">\n		                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "video", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n						\n                    	<article class=\"l-half carousel-content\">\n				            <h1>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</h1>\n				            <p>");
  hashContexts = {'unescaped': depth0};
  hashTypes = {'unescaped': "STRING"};
  stack1 = helpers._triageMustache.call(depth0, "body", {hash:{
    'unescaped': ("true")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</p>\n				            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "link_text", {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n				        </article>\n				        \n		        	</div>\n		        	\n		        	<div class=\"carousel-image\"></div>\n		        </li>\n		    ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n							<div class=\"l-half carousel-video\">\n	                			<div class=\"video\">");
  hashContexts = {'unescaped': depth0};
  hashTypes = {'unescaped': "STRING"};
  stack1 = helpers._triageMustache.call(depth0, "video", {hash:{
    'unescaped': ("true")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n							</div>\n						");
  return buffer;
  }

function program4(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n				                <a class=\"btn btn-primary\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "link_text", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</a>\n				            ");
  return buffer;
  }

function program6(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n	                        <li>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "tab_text", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</li>\n	                    ");
  return buffer;
  }

  data.buffer.push("<div class=\"l-section home-carousel\">\n		<section class=\"carousel\">\n			<ul>\n			");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "slides", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n			</ul>\n			\n	        <div class=\"l-section carousel-nav-section\">\n	            <div class=\"l-wrapper\">\n	                <ol class=\"carousel-nav l-full\">\n	                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "slides", {hash:{},inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                </ol>\n	            </div>\n	        </div>\n        </section>\n	</div>");
  return buffer;
  
});Ember.TEMPLATES['home_impact'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, self=this, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression;

function program1(depth0,data) {
  
  var buffer = '', stack1, stack2, hashContexts, hashTypes, options;
  data.buffer.push("\n                    ");
  hashContexts = {'classNames': depth0};
  hashTypes = {'classNames': "STRING"};
  options = {hash:{
    'classNames': ("btn-link")
  },inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "signup", options) : helperMissing.call(depth0, "linkTo", "signup", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                ");
  return buffer;
  }
function program2(depth0,data) {
  
  
  data.buffer.push("Join us. Sign up and share your 1%");
  }

  data.buffer.push("<div class=\"l-section home-impact\">\n        <section class=\"l-wrapper\">\n            <div class=\"l-full\">\n        \n                <header class=\"section-header\">\n            	    <h1>Our impact</h1>\n            	    <p>We believe that if we all share a little, together we can change the world. We got this far already.</p>\n                </header>\n\n                <ul class=\"impact\">\n                    <li class=\"impact-lives\">\n                    	<figure class=\"image\"><object type=\"image/svg+xml\" data=\"/static/assets/images/illustrations/lives-green.svg\" class=\"logo-image\"><img src=\"");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "STATIC_URL", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("images/global/countries-green.png\" alt=\"Countries\"></object></figure>\n                        <strong>");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "impact.lives_changed", options) : helperMissing.call(depth0, "localize", "impact.lives_changed", options))));
  data.buffer.push("</strong>\n                        Lives changed\n                    </li>\n                    <li class=\"impact-projects\">\n                    	<figure class=\"image\"><object type=\"image/svg+xml\" data=\"/static/assets/images/illustrations/ideas-pink.svg\" class=\"logo-image\"><img src=\"");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "STATIC_URL", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("images/global/countries-green.png\" alt=\"Countries\"></object></figure>\n                        <strong>");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "impact.projects", options) : helperMissing.call(depth0, "localize", "impact.projects", options))));
  data.buffer.push("</strong>\n                        Projects\n                    </li>\n                    <li class=\"impact-countries\">\n                    	<figure class=\"image\"><object type=\"image/svg+xml\" data=\"/static/assets/images/illustrations/countries-green.svg\" class=\"logo-image\"><img src=\"");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "STATIC_URL", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("images/global/countries-green.png\" alt=\"Countries\"></object></figure>\n                        <strong>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "impact.countries", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong>\n                        Countries\n                    </li>                    \n                    <li class=\"impact-hours\">\n                    	<figure class=\"image\"><object type=\"image/svg+xml\" data=\"/static/assets/images/illustrations/hours-pink.svg\" class=\"logo-image\"><img src=\"");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "STATIC_URL", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("images/global/countries-green.png\" alt=\"Countries\"></object></figure>\n                        <strong>");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "impact.hours_spent", options) : helperMissing.call(depth0, "localize", "impact.hours_spent", options))));
  data.buffer.push("</strong>\n                        Hours spent\n                    </li>\n                    <li class=\"impact-donated\">\n                    	<figure class=\"image\"><object type=\"image/svg+xml\" data=\"/static/assets/images/illustrations/donate-green.svg\" class=\"logo-image\"><img src=\"");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "STATIC_URL", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("images/global/countries-green.png\" alt=\"Countries\"></object></figure>\n                        <strong>&euro; ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "impact.donated", options) : helperMissing.call(depth0, "localize", "impact.donated", options))));
  data.buffer.push("</strong>\n                        Donated\n                    </li>\n                </ul>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers.unless.call(depth0, "controllers.currentUser.isAuthenticated", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n            </div>    \n            \n        </section>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['home_project'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, escapeExpression=this.escapeExpression, self=this, helperMissing=helpers.helperMissing;

function program1(depth0,data) {
  
  var hashTypes, hashContexts;
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  }

function program3(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                        <div class=\"project-days-left l-one-third\">\n    						<strong><span class=\"flaticon solid clock-1\"></span> ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.campaign.daysToGo", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong>\n    						<em>days to go</em>\n    					</div>\n    					");
  return buffer;
  }

  data.buffer.push("<div class=\"l-section home-projects\">\n        <section class=\"l-wrapper\">\n        	\n            <div class=\"project-slider l-full\">\n            	\n	        	<header class=\"section-header\">\n	            	<h1>Choose your project</h1>\n					<p>Support it with your time, knowledge or money and receive real-time updates.</p>\n	        	</header>\n\n                <div class=\"project-preview\">\n                    \n                    <figure class=\"image l-half\">\n                        <img>\n                    </figure>\n\n                    <article class=\"project-info l-half\">\n                        <div class=\"project-meta\">\n		                    <span class=\"project-location\"><span class=\"flaticon solid location-pin-1\"></span> ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.plan.country.name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</span>\n		                    <span class=\"project-theme\"><span class=\"flaticon solid tag-1\"></span> ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.plan.theme.title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</span>\n		                </div>\n		                \n                        <h2 class=\"project-title\">");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "project", "project.getProject", options) : helperMissing.call(depth0, "linkTo", "project", "project.getProject", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("</h2>\n                        <p class=\"project-description\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.plan.pitch", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>\n                    </article>\n                    \n                    <div class=\"project-status l-half\">\n                    \n                        ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "project.campaign.deadline", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n    					\n    					<div class=\"project-fund l-one-third\">\n                            <p class=\"project-fund-amount\">\n                                <strong class=\"amount-donated\">&euro;");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "project.campaign.money_donated", options) : helperMissing.call(depth0, "localize", "project.campaign.money_donated", options))));
  data.buffer.push("</strong>\n                                of\n                                <strong class=\"amount-asked\">&euro;");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "project.campaign.money_asked", options) : helperMissing.call(depth0, "localize", "project.campaign.money_asked", options))));
  data.buffer.push("</strong>\n                                raised\n                            </p>\n                        \n                            <div class=\"project-fund-amount-slider\"><strong style=\"width: 0%;\" class=\"slider-progress is-in-progress\"><em class=\"slider-percentage\">0%</em></strong></div>\n    					</div>\n                        \n                        <div class=\"project-action l-one-third\">\n    					    <a href=\"#\"><span class=\"flaticon solid wallet-1\"></span> Support</a>\n                        </div>\n                        \n					</div>\n                </div>\n                \n                <span>Previous project</span>\n                <span>Next project</span>\n                \n            </div>\n        </section>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['home_quotes'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, escapeExpression=this.escapeExpression, self=this, helperMissing=helpers.helperMissing;

function program1(depth0,data) {
  
  
  data.buffer.push("\n                    <span class=\"flaticon stroke zoom-2\"></span> Find projects\n                ");
  }

function program3(depth0,data) {
  
  
  data.buffer.push("\n                    <span class=\"flaticon solid wrench-1\"></span> Find tasks\n                ");
  }

  data.buffer.push("<div class=\"l-section home-quotes\">\n        <section class=\"l-wrapper\">\n            <div class=\"l-full\">\n            \n                <header class=\"section-header\">\n                	<h1>Share a little. <em>Change the world.</em></h1>\n            	</header>\n    \n                <div class=\"quote\">\n                    <figure>\n                        <img>\n                    </figure>\n    \n                    <article>\n                        <p class=\"quote-name\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "quote.user.full_name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>\n                        <p class=\"quote-content\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "quote.quote", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>\n                    </article>\n                </div>\n    \n                ");
  hashContexts = {'class': depth0};
  hashTypes = {'class': "STRING"};
  options = {hash:{
    'class': ("btn btn-iconed one")
  },inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "projectList", options) : helperMissing.call(depth0, "linkTo", "projectList", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n    \n    			");
  hashContexts = {'class': depth0};
  hashTypes = {'class': "STRING"};
  options = {hash:{
    'class': ("btn btn-iconed two")
  },inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "taskList", options) : helperMissing.call(depth0, "linkTo", "taskList", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n    \n                <a class=\"btn btn-iconed three\">\n                    <span class=\"flaticon solid heart-1\"></span> Befriend us\n                </a>\n            </div>\n        </section>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['map_picker'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', hashContexts, hashTypes, escapeExpression=this.escapeExpression;


  data.buffer.push("<div class=\"map-picker\"></div>\n    <div class=\"map-look-up\">\n        ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("view.lookup"),
    'placeholder': ("Search your location.")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n        <button> Search</button>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['media_wallpost_new'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.title", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program4(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.text", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }

function program6(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.video_url", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }

function program8(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <li class=\"form-wallpost-photo\">\n                                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "photo.errors", {hash:{},inverse:self.program(11, program11, data),fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                            </li>\n                        ");
  return buffer;
  }
function program9(depth0,data) {
  
  
  data.buffer.push("\n                                    <span class=\"message is-error\">Error</span>\n                                ");
  }

function program11(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "photo.photo.small", {hash:{},inverse:self.program(14, program14, data),fn:self.program(12, program12, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                                ");
  return buffer;
  }
function program12(depth0,data) {
  
  
  data.buffer.push("\n                                        <img>\n                                        <a><span class=\"flaticon solid x-2\"></span> <strong>Delete</strong></a>\n                                    ");
  }

function program14(depth0,data) {
  
  
  data.buffer.push("\n                                        <div class=\"is-loading-small\"><img src=\"images/loading.gif\"> <strong>Loading photos</strong></div>\n                                    ");
  }

  data.buffer.push("<fieldset>\n        <ul>\n            <li class=\"control-group\">\n                <label class=\"control-label\" for=\"wallpost-title\">\n                    Name of your update.\n                </label>\n\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'id': depth0,'name': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'id': "STRING",'name': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Ember.TextField", {hash:{
    'valueBinding': ("title"),
    'placeholder': ("Keep it short and simple"),
    'id': ("wallpost-title"),
    'name': ("wallpost-title"),
    'classBinding': ("errors.title.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.title", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n\n            <li class=\"control-group\">\n                <label class=\"control-label\" for=\"wallpost-update\">\n                    Your update.\n                </label>\n\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'cols': depth0,'rows': depth0,'name': depth0,'id': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'cols': "STRING",'rows': "STRING",'name': "STRING",'id': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Ember.TextArea", {hash:{
    'valueBinding': ("text"),
    'placeholder': ("Tell something about the progress, context or yourself!"),
    'cols': ("50"),
    'rows': ("4"),
    'name': ("wallpost-update"),
    'id': ("wallpost-update"),
    'classBinding': ("errors.text.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.text", {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n\n            <li class=\"control-group\">\n                <label class=\"control-label\" for=\"wallpost-video\">\n                    Add link to video\n                </label>\n\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'id': depth0,'name': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'id': "STRING",'name': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Ember.TextField", {hash:{
    'valueBinding': ("video_url"),
    'placeholder': ("Use YouTube or Vimeo"),
    'id': ("wallpost-video"),
    'name': ("wallpost-video"),
    'classBinding': ("errors.video_url.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.video_url", {hash:{},inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n\n            <li class=\"control-group\">\n                <label class=\"control-label\" for=\"wallpost-photo\">\n                    Upload photos<br>\n                    <small>format 620 x 380 minimum for best result</small>\n                </label>\n\n                <div class=\"controls\">\n                    <ul class=\"form-wallpost-photos\">\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "photo", "in", "files", {hash:{},inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </ul>\n                    \n                    <a class=\"btn-link btn-upload\">\n                        ");
  hashContexts = {'valueBinding': depth0,'multiple': depth0,'id': depth0,'name': depth0,'accept': depth0};
  hashTypes = {'valueBinding': "STRING",'multiple': "STRING",'id': "STRING",'name': "STRING",'accept': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.UploadMultipleFiles", {hash:{
    'valueBinding': ("photo_files"),
    'multiple': ("multiple"),
    'id': ("wallpost-photo"),
    'name': ("wallpost-photo"),
    'accept': ("image/*")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        <span class=\"flaticon solid upload-document-1\"></span>\n                        Upload photos\n                    </a>\n                </div>\n            </li>\n        </ul>\n    </fieldset>\n\n    <button class=\"btn btn-iconed\" type=\"submit\"><span class=\"flaticon solid thinking-comment-1\"></span>Post Update</button>");
  return buffer;
  
});Ember.TEMPLATES['monthlyDonation'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashContexts, hashTypes, options, escapeExpression=this.escapeExpression, self=this, helperMissing=helpers.helperMissing;

function program1(depth0,data) {
  
  var buffer = '', hashContexts, hashTypes;
  data.buffer.push("\n        <figure class=\"project-image\">\n            <img ");
  hashContexts = {'src': depth0,'alt': depth0};
  hashTypes = {'src': "STRING",'alt': "STRING"};
  data.buffer.push(escapeExpression(helpers.bindAttr.call(depth0, {hash:{
    'src': ("project.plan.image.square"),
    'alt': ("project.title")
  },contexts:[],types:[],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("  />\n        </figure>\n        <h2 class=\"project-title\">\n            ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n            <em class=\"project-location\">\n                <span class=\"flaticon solid location-pin-1\"></span> ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.plan.country.name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n            </em>\n        </h2>\n    ");
  return buffer;
  }

function program3(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                <span class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "error", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</span>\n            ");
  return buffer;
  }

  hashContexts = {'class': depth0};
  hashTypes = {'class': "STRING"};
  options = {hash:{
    'class': ("project-header")
  },inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "project", "project", options) : helperMissing.call(depth0, "linkTo", "project", "project", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n\n    <div class=\"fund-amount\">\n        <strong class=\"fund-amount-needed\">&euro; ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.campaign.money_needed", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong> is still needed\n        \n        <div class=\"fund-amount-divided\">\n            ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers.each.call(depth0, "error", "in", "errors.amount", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n            <strong>&euro; ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "amount", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong>\n        </div>\n    </div>\n    \n    <a><span class=\"flaticon solid x-2\"></span> <strong>Delete</strong></a></li>");
  return buffer;
  
});Ember.TEMPLATES['monthlyProjectList'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts, options;
  data.buffer.push("\n                    ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.render || depth0.render),stack1 ? stack1.call(depth0, "monthlyProjectPreview", "project", options) : helperMissing.call(depth0, "render", "monthlyProjectPreview", "project", options))));
  data.buffer.push("\n                ");
  return buffer;
  }

function program3(depth0,data) {
  
  
  data.buffer.push("\n                    <li class=\"no-results\">No projects found.</li>\n                ");
  }

  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.render || depth0.render),stack1 ? stack1.call(depth0, "monthlyProjectSearchForm", options) : helperMissing.call(depth0, "render", "monthlyProjectSearchForm", options))));
  data.buffer.push("\n    <article>\n        <header>\n            <ul id=\"search-results\">\n                ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers.each.call(depth0, "project", "in", "model", {hash:{},inverse:self.program(3, program3, data),fn:self.program(1, program1, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n            </ul>\n            </header>\n    </article>");
  return buffer;
  
});Ember.TEMPLATES['monthlyProjectPreview'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  
  data.buffer.push("\n                    <span class=\"project-phase\"><span class=\"flaticon solid lightbulb-3\"></span> <strong>New</strong> <em>Smart Idea</em></span> \n	            ");
  }

function program3(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "project.campaign.money_asked", {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "project.campaign.deadline", {hash:{},inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	            ");
  return buffer;
  }
function program4(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts, options;
  data.buffer.push("\n                        <div class=\"project-fund-amount-slider\"><strong style=\"width: 0%;\" class=\"slider-progress is-in-progress\"><em class=\"slider-percentage\">0%</em></strong></div>\n                        <span class=\"project-fund-amount\"><strong>&euro;");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "project.campaign.money_needed", options) : helperMissing.call(depth0, "localize", "project.campaign.money_needed", options))));
  data.buffer.push("</strong> <em>To go</em></span>\n                    ");
  return buffer;
  }

function program6(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                        <span class=\"project-days-left\"><span class=\"flaticon solid clock-1\"></span> <strong>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.campaign.daysToGo", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong> <em>days</em></span>\n                    ");
  return buffer;
  }

  data.buffer.push("<li class=\"project-item project-item-small\">\n    \n        <a ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.action.call(depth0, "addProjectToMonthly", "project.getProject", {hash:{},contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(">\n            <span class=\"project-header\">\n            \n            	<figure class=\"project-image\">\n                	<img ");
  hashContexts = {'src': depth0};
  hashTypes = {'src': "STRING"};
  data.buffer.push(escapeExpression(helpers.bindAttr.call(depth0, {hash:{
    'src': ("project.image")
  },contexts:[],types:[],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("  />\n            	</figure>\n            	\n                <span class=\"project-title\">\n                	<h3>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</h3>\n                    <span class=\"project-location\"><span class=\"flaticon solid location-pin-1\"></span> ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.country.name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</span> \n                </span>\n            </span>\n            \n	        <span class=\"project-status campaign\">\n	            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "project.isPhasePlan", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	\n	            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "project.isPhaseCampaign", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	        </span>\n	        \n            <span class=\"project-description\">");
  hashContexts = {'unescaped': depth0};
  hashTypes = {'unescaped': "STRING"};
  stack1 = helpers._triageMustache.call(depth0, "pitch", {hash:{
    'unescaped': ("true")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</span>\n	        \n        </a>\n    </li>");
  return buffer;
  
});Ember.TEMPLATES['monthlyProjectSearchForm'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  
  data.buffer.push("\n		                    <a>\n		                        <span class=\"flaticon solid left-circle-2\"></span>\n		                    </a>\n		                ");
  }

function program3(depth0,data) {
  
  
  data.buffer.push("\n		                	<span class=\"previous-page\"><span class=\"flaticon solid left-circle-2\"></span></span>\n		                ");
  }

function program5(depth0,data) {
  
  
  data.buffer.push("\n		                    <a>\n		                        <span class=\"flaticon solid right-circle-2\"></span>\n		                    </a>\n		                ");
  }

function program7(depth0,data) {
  
  
  data.buffer.push("\n		                	<span class=\"next-page\"><span class=\"flaticon solid right-circle-2\"></span></span>\n		                ");
  }

  data.buffer.push("<div id=\"search\">\n        <section>\n            <form id=\"search-form\">\n                <div class=\"control\">\n                    ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("text"),
    'placeholder': ("Search")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    <span class=\"flaticon stroke zoom-2\"></span>\n                </div>\n                <div class=\"control\">\n                    ");
  hashContexts = {'valueBinding': depth0};
  hashTypes = {'valueBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.ProjectCountrySelectView", {hash:{
    'valueBinding': ("country")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    <span class=\"flaticon solid earth-1\"></span>\n                </div>\n                <div class=\"control\">\n                    ");
  hashContexts = {'valueBinding': depth0};
  hashTypes = {'valueBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.ThemeSelectView", {hash:{
    'valueBinding': ("theme")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    <span class=\"flaticon stroke tag-2\"></span>\n                </div>\n            </form>\n        </section>\n    </div>\n\n    <div>\n        <section>\n            <article id=\"search-navigation\">\n            	\n            	<header>\n                	<h4>Found <em>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "controllers.monthlyProjectList.model.meta.total", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</em></h4>\n                    <a>\n                        <span class=\"flaticon solid x-2\"></span> Reset Search Filter\n                    </a>\n            	</header>\n                \n                <div class=\"search-sort\">\n                    Sort:\n                    <a>Most popular</a>\n                    \n                    <a>Newest</a>\n                    <a>Almost funded</a>\n                    <a>Near deadline</a>\n                </div>\n                \n                <div class=\"search-pagination\">\n                	<span class=\"search-showing\">Showing ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "rangeStart", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("-");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "rangeEnd", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</span>\n                	<span class=\"search-pages-control\">\n		                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "hasPreviousPage", {hash:{},inverse:self.program(3, program3, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n		                \n		                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "hasNextPage", {hash:{},inverse:self.program(7, program7, data),fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                	</span>\n                </div>\n                \n            </article>\n        </section>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['my_pitch_basics'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.title", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program4(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.pitch", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }

function program6(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.description", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }

function program8(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.theme", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }

function program10(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.tags", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }

function program12(depth0,data) {
  
  var buffer = '', hashContexts, hashTypes;
  data.buffer.push("\n                        <label class=\"radio\">");
  hashContexts = {'value': depth0};
  hashTypes = {'value': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': ("skills")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("<span>Skills and expertise</span></label>\n                        <label class=\"radio\">");
  hashContexts = {'value': depth0};
  hashTypes = {'value': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': ("finance")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("<span>Crowdfunding campaign</span></label>\n                        <label class=\"radio\">");
  hashContexts = {'value': depth0};
  hashTypes = {'value': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': ("both")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("<span>Both</span></label>\n                    ");
  return buffer;
  }

  data.buffer.push("<legend>\n        <strong>Pitch basics</strong>\n    </legend>\n\n    <fieldset>\n        <ul>\n            <li class=\"control-group has-popover\" data-content=\"Be short, creative, simple and memorable.\">\n                <label class=\"control-label\">Title</label>\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("title"),
    'placeholder': ("Title"),
    'classBinding': ("errors.title.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.title", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n\n            <li class=\"control-group has-popover\" data-content=\"By reading your pitch many donors already make the decision to donate or not. The explanation must be to the point, because people don't have time to read everything.\">\n                <label class=\"control-label\">Pitch</label>\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextArea", {hash:{
    'valueBinding': ("pitch"),
    'placeholder': ("Description"),
    'classBinding': ("errors.pitch.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.pitch", {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n\n            <li class=\"control-group has-popover\" data-content=\"A short description should at least tell something about a person, place, mitvation and activity. The simplest story would be: [Person] in [place] needs help to [activity] because [motivation].\">\n                <label class=\"control-label wide\">Short explanation: Why, what and how</label>\n                <div class=\"controls wide\">\n                    ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0,'rows': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING",'rows': "INTEGER"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextArea", {hash:{
    'valueBinding': ("description"),
    'classBinding': ("errors.description.length:error"),
    'rows': (12)
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.description", {hash:{},inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n        </ul>\n    </fieldset>\n    \n    <fieldset>\n        <ul>\n            <li class=\"control-group has-popover\" data-content=\"Select one of the themes.\">\n                <label class=\"control-label\">Theme</label>\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.ThemeSelectView", {hash:{
    'valueBinding': ("theme"),
    'classBinding': ("errors.theme.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.theme", {hash:{},inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n        </ul>\n    </fieldset>\n    \n    <fieldset>\n        <ul>\n            <li class=\"control-group\">\n                <label class=\"control-label\">\n                    Tags (");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "tags.length", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(")<br>\n                    <small>Between 2 and 5 tags</small>\n                </label>\n\n                <div class=\"controls\">\n                    ");
  hashContexts = {'tagsBinding': depth0,'classBinding': depth0};
  hashTypes = {'tagsBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.TagWidget", {hash:{
    'tagsBinding': ("tags"),
    'classBinding': ("errors.tags.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.tags", {hash:{},inverse:self.noop,fn:self.program(10, program10, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n        </ul>\n    </fieldset>\n    \n    <fieldset>\n        <ul>   \n            <li class=\"control-group has-popover\" data-content=\"What do you need to realise your smart idea?\">\n                <label class=\"control-label\">\n                    What do you need?\n                </label>\n\n                <div class=\"controls\">\n                    ");
  hashContexts = {'name': depth0,'selectedValueBinding': depth0,'class': depth0};
  hashTypes = {'name': "STRING",'selectedValueBinding': "STRING",'class': "STRING"};
  stack1 = helpers.view.call(depth0, "Em.RadioButtonGroup", {hash:{
    'name': ("need"),
    'selectedValueBinding': ("need"),
    'class': ("radio-group")
  },inverse:self.noop,fn:self.program(12, program12, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </div>\n            </li>\n        </ul>\n    </fieldset>\n\n    <button><span class=\"flaticon solid right-2\"></span>Save & Next</button>");
  return buffer;
  
});Ember.TEMPLATES['my_pitch_index'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashContexts, hashTypes, options, self=this, helperMissing=helpers.helperMissing;

function program1(depth0,data) {
  
  
  data.buffer.push("<span class=\"flaticon solid right-2\"></span>Next");
  }

  data.buffer.push("<fieldset>\n        <legend>\n        	<strong>Get ready to write your pitch!</strong>\n			<p>Time to pitch your smart idea because we just can’t wait to hear about it! Make sure your story is positive, convincing and compelling. Fill in the Projects Basics, Location and a Picture. Need more tips and tricks to blow us away with your pitch? Check out our <a href=\"/#!/pages/faq-projects\">FAQ</a>.</p>\n        </legend>\n    </fieldset>\n\n    ");
  hashContexts = {'class': depth0};
  hashTypes = {'class': "STRING"};
  options = {hash:{
    'class': ("btn btn-iconed btn-next")
  },inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectPitch.basics", options) : helperMissing.call(depth0, "linkTo", "myProjectPitch.basics", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  return buffer;
  
});Ember.TEMPLATES['my_pitch_new'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, self=this, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.detail", {hash:{},inverse:self.program(5, program5, data),fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', stack1, stack2, hashContexts, hashTypes, options;
  data.buffer.push("\n                        <p class=\"alert alert-error\">\n                            Problem creating pitch.\n                        </p>\n                        It looks like you already have started a project in progress. You can manage your project here:\n                        ");
  hashContexts = {'tagName': depth0,'class': depth0};
  hashTypes = {'tagName': "STRING",'class': "STRING"};
  options = {hash:{
    'tagName': ("button"),
    'class': ("btn btn-primary btn-iconed")
  },inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectList", options) : helperMissing.call(depth0, "linkTo", "myProjectList", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n\n                    ");
  return buffer;
  }
function program3(depth0,data) {
  
  
  data.buffer.push("\n                            <span class=\"flaticon solid pencil-3\"></span>\n                            Manage projects.\n                        ");
  }

function program5(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n                        <form id=\"manage-project-new\">\n                            <fieldset>\n                                <ul>\n                                    <li class=\"control-group\">\n                                        <label class=\"control-label\">Name your pitch</label>\n                                        <div class=\"controls\">\n                                            ");
  hashContexts = {'valueBinding': depth0,'name': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'name': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("title"),
    'name': ("title"),
    'placeholder': ("Title for your smart idea"),
    'classBinding': ("errors.title.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                                        </div>\n                                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.title", {hash:{},inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                                    </li>\n                                </ul>\n                            </fieldset>\n                            \n                            <button>\n                                <em class=\"flaticon solid pencil-3\"></em>write your pitch\n                            </button>\n                        </form>\n                    ");
  return buffer;
  }
function program6(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.title", {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                                        ");
  return buffer;
  }
function program7(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program9(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n                    <p class=\"login-signup\"><a href=\"/accounts/login\">Login</a> or become a ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(10, program10, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "signup", options) : helperMissing.call(depth0, "linkTo", "signup", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push(" to pitch your plan.</p>\n                ");
  return buffer;
  }
function program10(depth0,data) {
  
  
  data.buffer.push("member");
  }

  data.buffer.push("<div class=\"l-section\" id=\"project-dashboard\">\n    	\n    	");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.partial || depth0.partial),stack1 ? stack1.call(depth0, "my_project_top", options) : helperMissing.call(depth0, "partial", "my_project_top", options))));
  data.buffer.push("\n    \n        <div class=\"l-wrapper\">\n            <div class=\"l-content\">\n            \n                <header class=\"l-page-header\">\n                    <h1> Send in your Project Pitch</h1>\n                    <p><strong>\n\nDo you have a smart idea to make a contribution to your community? An idea to tackle a waste problem in your neighborhood? An idea for clean and green transport? An idea to use tech innovations to improve local healthcare? Well, you came to the right place. We LOVE smart ideas!\n\n                    </strong></p>\n                </header>\n\n                <p>\n\n1%Club offers you tools to engage your crowd to turn your smart idea in to reality.<br>\nAre you ready to invest time and effort in succeeding? Double check our <a href=\"/#!/pages/faq-projects\">FAQ</a> and pitch your smart idea here!\n\n                </p>\n                \n                ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "controllers.currentUser.isAuthenticated", {hash:{},inverse:self.program(9, program9, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n            </div>\n            <sidebar class=\"l-sidebar\">\n                <h3>WHEN YOUR SMART IDEA...</h3>\n                <ul>\n                    <li>Might seem small, but will have a big social impact</li>\n                    <li>Is concrete and thus has a clear start and end</li>\n                    <li>Needs on off investment to make it self-sufficient and sustainable on the long term</li>\n                    <li>Takes place in one of these developing countries</li>\n                    <li>Is managed and owned locally</li>\n                    <li>Needs people, special know-how and skills</li>\n                    <li>Needs some cash to get started (up to €5000)</li>\n                </ul>\n                ...your idea fits right in with 1%Club!\n            </sidebar>\n        </div>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['my_pitch_submit'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, self=this, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression;

function program1(depth0,data) {
  
  
  data.buffer.push("\n                <h3><span class=\"flaticon solid checkmark-1\"></span> Basics are ok!<br></h3>\n            ");
  }

function program3(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n                <h3>");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectPitch.basics", options) : helperMissing.call(depth0, "linkTo", "myProjectPitch.basics", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push(" still need work!</h3>\n                ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers.unless.call(depth0, "title", {hash:{},inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers.unless.call(depth0, "pitch", {hash:{},inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers.unless.call(depth0, "theme", {hash:{},inverse:self.noop,fn:self.program(10, program10, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers.unless.call(depth0, "description", {hash:{},inverse:self.noop,fn:self.program(12, program12, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers.unless.call(depth0, "tags", {hash:{},inverse:self.noop,fn:self.program(14, program14, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n            ");
  return buffer;
  }
function program4(depth0,data) {
  
  
  data.buffer.push("Basics");
  }

function program6(depth0,data) {
  
  
  data.buffer.push("\n                    <span class=\"flaticon solid exclamation-point-2\"></span> <strong>Title</strong> is missing<br>\n                ");
  }

function program8(depth0,data) {
  
  
  data.buffer.push("\n                    <span class=\"flaticon solid exclamation-point-2\"></span> <strong>Pitch</strong> is missing<br>\n                ");
  }

function program10(depth0,data) {
  
  
  data.buffer.push("\n                    <span class=\"flaticon solid exclamation-point-2\"></span> <strong>Theme</strong> is missing<br>\n                ");
  }

function program12(depth0,data) {
  
  
  data.buffer.push("\n                    <span class=\"flaticon solid exclamation-point-2\"></span> <strong>Why, what and how</strong> is missing<br>\n                ");
  }

function program14(depth0,data) {
  
  
  data.buffer.push("\n                    <span class=\"flaticon solid exclamation-point-2\"></span> <strong>Tags</strong> are missing. Add at least five tags.<br>\n                ");
  }

function program16(depth0,data) {
  
  
  data.buffer.push("\n                <h3><span class=\"flaticon solid checkmark-1\"></span> Location is ok!</h3>\n            ");
  }

function program18(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n                <h3>");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectPitch.basics", options) : helperMissing.call(depth0, "linkTo", "myProjectPitch.basics", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push(" still need work!</h4>\n                ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers.unless.call(depth0, "latitude", {hash:{},inverse:self.noop,fn:self.program(19, program19, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers.unless.call(depth0, "country", {hash:{},inverse:self.noop,fn:self.program(21, program21, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n            ");
  return buffer;
  }
function program19(depth0,data) {
  
  
  data.buffer.push("\n                    <span class=\"flaticon solid exclamation-point-2\"></span> <strong>Map location</strong> is missing<br>\n                ");
  }

function program21(depth0,data) {
  
  
  data.buffer.push("\n                    <span class=\"flaticon solid exclamation-point-2\"></span> <strong>Country</strong> are missing<br>\n                ");
  }

function program23(depth0,data) {
  
  
  data.buffer.push("\n                <h3><span class=\"flaticon solid checkmark-1\"></span> Media is ok!</h3>\n            ");
  }

function program25(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n                <h3>");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(26, program26, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectPitch.media", options) : helperMissing.call(depth0, "linkTo", "myProjectPitch.media", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push(" still need work!</h3>\n                <span class=\"flaticon solid exclamation-point-2\"></span> <strong>Image</strong> is missing<br>\n            ");
  return buffer;
  }
function program26(depth0,data) {
  
  
  data.buffer.push("Media");
  }

function program28(depth0,data) {
  
  
  data.buffer.push("\n        <button><span class=\"flaticon solid right-2\"></span>Submit pitch</button>\n    ");
  }

  data.buffer.push("<legend>\n        <strong>Submit Pitch</strong>\n        <p>Send your pitch to us, we'll get back to you soon.</p>\n    </legend>\n    \n    <fieldset>\n    \n        <div class=\"manage-project-overview\">\n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "validBasics", {hash:{},inverse:self.program(3, program3, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "validLocation", {hash:{},inverse:self.program(18, program18, data),fn:self.program(16, program16, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "validMedia", {hash:{},inverse:self.program(25, program25, data),fn:self.program(23, program23, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n        </div>\n        \n        <ul> \n            <li class=\"control-group has-popover\" data-content=\"Agree to the terms to submit the pitch\">\n                <div class=\"controls wide\">\n                    <label class=\"checkbox\">");
  hashContexts = {'checkedBinding': depth0,'classBinding': depth0};
  hashTypes = {'checkedBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.Checkbox", {hash:{
    'checkedBinding': ("agreed"),
    'classBinding': ("errors.agreed.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" <span>I agree to the  <a>general terms and conditions</a></span></label>\n                </div>\n            </li>\n        </ul>\n\n    </fieldset>\n    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "agreed", {hash:{},inverse:self.program(28, program28, data),fn:self.program(28, program28, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  return buffer;
  
});Ember.TEMPLATES['my_project'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, options, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression;


  data.buffer.push("<div class=\"l-section\" id=\"manage-project\">\n    	");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.partial || depth0.partial),stack1 ? stack1.call(depth0, "my_project_top", options) : helperMissing.call(depth0, "partial", "my_project_top", options))));
  data.buffer.push("\n		");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "outlet", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	</div>");
  return buffer;
  
});Ember.TEMPLATES['my_project_campaign'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, escapeExpression=this.escapeExpression, self=this, helperMissing=helpers.helperMissing;

function program1(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("your 1%COACH, <strong>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "coach.full_name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong>, at");
  return buffer;
  }

function program3(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                        <div class=\"project-days-left\">\n						    <strong><span class=\"flaticon solid clock-1\"></span> ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "campaign.daysToGo", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong>\n                            <em>days to go</em>\n                        </div>\n                    ");
  return buffer;
  }

function program5(depth0,data) {
  
  
  data.buffer.push("\n                    <em class=\"flaticon solid wrench-1\"></em>\n                    Create a new task\n                ");
  }

function program7(depth0,data) {
  
  
  data.buffer.push("\n                    <span class=\"flaticon solid megaphone-1\"></span>\n                    Post an Update\n                ");
  }

  data.buffer.push("<div class=\"l-wrapper\">\n    \n        <div class=\"manage-project-sidebar\">\n\n            <h4><span class=\"flaticon solid lock-1\"></span> Project Story</h4>\n            <p>Your plan is approved and currently locked. If you need to make any changes: please sent a message to\n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "coach", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push(" projects@1procentclub.nl.</p>\n            \n            <h4><span class=\"flaticon solid wallet-1\"></span> Funding status</h4>\n                  \n            <div class=\"project-fund\">\n                <p class=\"project-fund-amount\">\n                    <strong class=\"amount-donated\">&euro;");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "campaign.money_donated", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong>\n                    of\n                    <strong class=\"amount-asked\">&euro;");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "campaign.money_asked", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong>\n                    raised\n                </p>\n            \n                <div class=\"project-fund-amount-slider\"><strong style=\"width: 0%;\" class=\"slider-progress is-in-progress\"><em class=\"slider-percentage\">0%</em></strong></div>\n			</div>\n        </div>\n\n        <form class=\"l-content manage-project-status\">\n            <fieldset>\n                <legend>\n                    <strong>How is your campaign going?</strong>\n                </legend>\n                \n                <div class=\"fieldset-content\">\n                    <p>\n                    Is money pouring in? No? Our tips & tricks might help you.\n                    Check our <a href=\"/#!/pages/faq-projects\">FAQ</a>! And remember Einsteins words: \"You have to learn the rules\n                    of the game. And then you have to play better than anyone else\".\n                    You can do it!\n                    </p>\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "campaign.deadline", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </div>\n            </fieldset>\n        </form>\n\n        <div class=\"toolbox\">\n            <h3 class=\"toolbox-title\">\n                <em class=\"flaticon solid wrench-1\"></em>\n                Crowdsourcing\n            </h3>\n            <div class=\"toolbox-content\">\n                <p>Do you need someone to help writing your business plan?</p>\n                ");
  hashContexts = {'tagName': depth0,'class': depth0};
  hashTypes = {'tagName': "STRING",'class': "STRING"};
  options = {hash:{
    'tagName': ("button"),
    'class': ("btn btn-iconed")
  },inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "projectTaskNew", "getProject", options) : helperMissing.call(depth0, "linkTo", "projectTaskNew", "getProject", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n            </div>\n        </div>\n\n        <div class=\"toolbox\">\n            <h3 class=\"toolbox-title\">\n                <em class=\"flaticon solid megaphone-1\"></em>\n                Project Updates\n            </h3>\n            <div class=\"toolbox-content\">\n                <p>Why not? Ask the crowd for feedback on your idea!</p>\n                ");
  hashContexts = {'tagName': depth0,'class': depth0};
  hashTypes = {'tagName': "STRING",'class': "STRING"};
  options = {hash:{
    'tagName': ("button"),
    'class': ("btn btn-iconed")
  },inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "project", "getProject", options) : helperMissing.call(depth0, "linkTo", "project", "getProject", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n            </div>\n        </div>\n\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['my_project_list'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, self=this, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression;

function program1(depth0,data) {
  
  
  data.buffer.push("\n                <div class=\"is-loading-big\"><img src=\"images/loading.gif\"  /> <strong>Loading projects</strong></div>\n            ");
  }

function program3(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "canPitchNew", {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            ");
  return buffer;
  }
function program4(depth0,data) {
  
  var buffer = '', stack1, stack2, hashContexts, hashTypes, options;
  data.buffer.push("\n                    <div class=\"l-content\">                        \n                        <header class=\"l-page-header\">\n                            <h1>No open projects</h1>\n                            <p></p>\n                        </header>\n                        \n                        ");
  hashContexts = {'tagName': depth0,'class': depth0};
  hashTypes = {'tagName': "STRING",'class': "STRING"};
  options = {hash:{
    'tagName': ("button"),
    'class': ("btn btn-primary btn-iconed")
  },inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myPitchNew", options) : helperMissing.call(depth0, "linkTo", "myPitchNew", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                    </div>\n                ");
  return buffer;
  }
function program5(depth0,data) {
  
  
  data.buffer.push("\n                            <span class=\"flaticon solid lightbulb-3\"></span>\n                            Pitch a new smart idea\n                        ");
  }

function program7(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                <li class=\"project-list-item\">\n                                    \n                        <span class=\"project-header\">\n                            <figure class=\"project-image\">\n                                <img>\n                            </figure>\n                            <h2 class=\"project-title\">\n                                ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("                                \n                                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "project.isPublic", {hash:{},inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                            </h2>\n                        </span>\n                        \n				        <div class=\"project-actions\">\n				        	Phase: <strong>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.phase", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong> | \n			                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "project.isPhasePitch", {hash:{},inverse:self.noop,fn:self.program(10, program10, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	\n	                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "project.isPhasePlan", {hash:{},inverse:self.noop,fn:self.program(16, program16, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	\n	                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "project.isPhaseCampaign", {hash:{},inverse:self.noop,fn:self.program(19, program19, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n				        </div>\n				    </li>\n					");
  return buffer;
  }
function program8(depth0,data) {
  
  
  data.buffer.push("\n                                    <a>\n    	                                <span class=\"flaticon solid eye-1\"></span>\n    	                                View public page\n    	                            </a>\n                                ");
  }

function program10(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n			                	Status: <strong>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.plan.status", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong>\n                                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "project.pitch.isBeingReviewed", {hash:{},inverse:self.program(13, program13, data),fn:self.program(11, program11, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                        ");
  return buffer;
  }
function program11(depth0,data) {
  
  
  data.buffer.push("\n								Your pitch is in review now.\n								  <br>\n								  We'll get back to you soon! \n								");
  }

function program13(depth0,data) {
  
  var buffer = '', stack1, stack2, hashContexts, hashTypes, options;
  data.buffer.push("\n	                              ");
  hashContexts = {'tagName': depth0,'class': depth0};
  hashTypes = {'tagName': "STRING",'class': "STRING"};
  options = {hash:{
    'tagName': ("a"),
    'class': ("btn btn-iconed")
  },inverse:self.noop,fn:self.program(14, program14, data),contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectPitch.basics", "project", options) : helperMissing.call(depth0, "linkTo", "myProjectPitch.basics", "project", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n								");
  return buffer;
  }
function program14(depth0,data) {
  
  
  data.buffer.push("\n	                                <span class=\"flaticon solid pencil-3\"></span>\n	                                Continue pitch\n	                              ");
  }

function program16(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n	                            Status: <strong>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.plan.status", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong>\n	                            ");
  hashContexts = {'tagName': depth0,'class': depth0};
  hashTypes = {'tagName': "STRING",'class': "STRING"};
  options = {hash:{
    'tagName': ("a"),
    'class': ("btn btn-iconed right")
  },inverse:self.noop,fn:self.program(17, program17, data),contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectPlan", "project", options) : helperMissing.call(depth0, "linkTo", "myProjectPlan", "project", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n	                        ");
  return buffer;
  }
function program17(depth0,data) {
  
  
  data.buffer.push("\n	                                <span class=\"flaticon solid pencil-3\"></span>\n	                                Continue plan\n	                            ");
  }

function program19(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n	                            Status: <strong>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.campaign.status", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong>\n	                            ");
  hashContexts = {'tagName': depth0,'class': depth0};
  hashTypes = {'tagName': "STRING",'class': "STRING"};
  options = {hash:{
    'tagName': ("a"),
    'class': ("btn btn-iconed right")
  },inverse:self.noop,fn:self.program(20, program20, data),contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectCampaign", "project", options) : helperMissing.call(depth0, "linkTo", "myProjectCampaign", "project", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n	                        ");
  return buffer;
  }
function program20(depth0,data) {
  
  
  data.buffer.push("\n	                                <span class=\"flaticon solid pencil-3\"></span>\n	                                Campaigning\n	                            ");
  }

  data.buffer.push("<div class=\"l-section\" id=\"project-dashboard\">\n    \n    	");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.partial || depth0.partial),stack1 ? stack1.call(depth0, "my_project_top", options) : helperMissing.call(depth0, "partial", "my_project_top", options))));
  data.buffer.push("\n    	\n        <div class=\"l-wrapper\">\n            ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "isLoading", {hash:{},inverse:self.program(3, program3, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n            \n            <div class=\"l-content\">\n	            <ul class=\"project-list\">\n	            	");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers.each.call(depth0, "project", "in", "controller", {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n	            </ul>\n			</div>\n        </div>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['my_project_location'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.country", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

  data.buffer.push("<legend>\n        <strong>Project location</strong>\n        <p>So where is it all happenin'?</p>\n    </legend>\n\n    <fieldset>\n        <ul>\n            <li class=\"control-group\">\n                <label class=\"control-label\">Country</label>\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.ProjectCountrySelectView", {hash:{
    'valueBinding': ("country"),
    'classBinding': ("errors.country.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.country", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n            <li class=\"control-group has-popover\" data-content=\"Select the location on the map. You can use the search to find your location.\">\n                <label class=\"control-label\">Location</label>\n                <div class=\"controls wide\">\n                    ");
  hashContexts = {'longitudeBinding': depth0,'latitudeBinding': depth0,'classBinding': depth0};
  hashTypes = {'longitudeBinding': "STRING",'latitudeBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.MapPicker", {hash:{
    'longitudeBinding': ("longitude"),
    'latitudeBinding': ("latitude"),
    'classBinding': ("errors.location.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n            </li>\n        </ul>\n    </fieldset>\n\n    <button><span class=\"flaticon solid right-2\"></span>Save & Next</button>");
  return buffer;
  
});Ember.TEMPLATES['my_project_pitch'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, self=this, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression;

function program1(depth0,data) {
  
  
  data.buffer.push("\n                        <em></em>\n                        Project Basics\n                    ");
  }

function program3(depth0,data) {
  
  
  data.buffer.push("\n                        <em></em>\n                        Location\n                    ");
  }

function program5(depth0,data) {
  
  
  data.buffer.push("\n                        <em></em>\n                        Media\n                    ");
  }

function program7(depth0,data) {
  
  
  data.buffer.push("\n                <span class=\"flaticon solid right-2\"></span>\n                Submit Pitch\n            ");
  }

  data.buffer.push("<div class=\"l-wrapper\">\n    \n        <div class=\"manage-project-sidebar\">\n            \n            <h4><em class=\"flaticon solid lightbulb-3\"></em>Project Pitch</h4>\n                \n            <ul class=\"manage-project-nav\">\n                <li>\n                    ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectPitch.basics", options) : helperMissing.call(depth0, "linkTo", "myProjectPitch.basics", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                </li>\n                <li>\n                    ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectPitch.location", options) : helperMissing.call(depth0, "linkTo", "myProjectPitch.location", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                </li>\n                <li>\n                    ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectPitch.media", options) : helperMissing.call(depth0, "linkTo", "myProjectPitch.media", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                </li>\n            </ul>\n            \n            ");
  hashContexts = {'class': depth0};
  hashTypes = {'class': "STRING"};
  options = {hash:{
    'class': ("btn btn-iconed btn-primary btn-submit")
  },inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectPitch.submit", options) : helperMissing.call(depth0, "linkTo", "myProjectPitch.submit", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n        </div>\n            \n        <form class=\"l-content\">\n            ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "outlet", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n        </form>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['my_project_pitch_approved'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, self=this, helperMissing=helpers.helperMissing;

function program1(depth0,data) {
  
  
  data.buffer.push("Project Plan");
  }

  data.buffer.push("<div class=\"l-wrapper\">\n        <article class=\"l-content\">\n            <header class=\"l-page-header\">\n                <h2>Yeah! Your pitch has been approved</h2>\n                <p>You can write your ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectPlan", options) : helperMissing.call(depth0, "linkTo", "myProjectPlan", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("!</p>\n            </header>\n        </article>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['my_project_pitch_rejected'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  


  data.buffer.push("<div class=\"l-wrapper\">\n        <article class=\"l-content\">\n            <header class=\"l-page-header\">\n                <h2>We're sorry, your pitch has been rejected</h2>\n                <p>Please contact us if you need support to define your smart idea.</p>\n            </header>\n        </article>\n    </div>");
  
});Ember.TEMPLATES['my_project_pitch_review'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  


  data.buffer.push("<div class=\"l-wrapper\">\n        <article class=\"l-content\">\n            <header class=\"l-page-header\">\n                <h2>Your pitch is in review now</h2>\n                <p>We'll get back to you soon!</p>\n            </header>\n        </article>\n    </div>");
  
});Ember.TEMPLATES['my_project_plan'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, self=this, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression;

function program1(depth0,data) {
  
  
  data.buffer.push("\n                            <em></em>\n                            Project Basics\n                        ");
  }

function program3(depth0,data) {
  
  
  data.buffer.push("\n                            <em></em>\n                            Project Description\n                        ");
  }

function program5(depth0,data) {
  
  
  data.buffer.push("\n                            <em></em>\n                            Location\n                        ");
  }

function program7(depth0,data) {
  
  
  data.buffer.push("\n                            <em></em>\n                            Media\n                        ");
  }

function program9(depth0,data) {
  
  
  data.buffer.push("\n                            <em></em>\n                            Organisation Profile\n                        ");
  }

function program11(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n                    <li>\n                        ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(12, program12, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectPlan.legal", options) : helperMissing.call(depth0, "linkTo", "myProjectPlan.legal", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                    </li>\n                    <li>\n                        ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(14, program14, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectPlan.ambassadors", options) : helperMissing.call(depth0, "linkTo", "myProjectPlan.ambassadors", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                    </li>\n                    ");
  return buffer;
  }
function program12(depth0,data) {
  
  
  data.buffer.push("\n                            <em></em>\n                            Legal Status\n                        ");
  }

function program14(depth0,data) {
  
  
  data.buffer.push("\n                            <em></em>\n                            Ambassadors\n                        ");
  }

function program16(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n                    <h4><span class=\"flaticon solid wallet-1\"></span> Crowdfunding</h4>\n                    <ul class=\"manage-project-nav\">\n                        <li>\n                            ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(17, program17, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectPlan.campaign", options) : helperMissing.call(depth0, "linkTo", "myProjectPlan.campaign", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                        </li>\n                        <li>\n                            ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(19, program19, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectPlan.budget", options) : helperMissing.call(depth0, "linkTo", "myProjectPlan.budget", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                        </li>\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "organization", {hash:{},inverse:self.noop,fn:self.program(21, program21, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                ");
  return buffer;
  }
function program17(depth0,data) {
  
  
  data.buffer.push("\n                                <em></em>\n                                Start Campaign\n                            ");
  }

function program19(depth0,data) {
  
  
  data.buffer.push("\n                                <em></em>\n                                Budget\n                            ");
  }

function program21(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n                        <li>\n                            ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(22, program22, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectPlan.bank", options) : helperMissing.call(depth0, "linkTo", "myProjectPlan.bank", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                        </li>\n                        ");
  return buffer;
  }
function program22(depth0,data) {
  
  
  data.buffer.push("\n                                <em></em>\n                                Bank details\n                            ");
  }

function program24(depth0,data) {
  
  
  data.buffer.push("\n                    <span class=\"flaticon solid right-2\"></span>\n                    Submit Plan\n                ");
  }

function program26(depth0,data) {
  
  
  data.buffer.push("\n                        <em class=\"flaticon solid wrench-1\"></em>\n                        Create a new task\n                    ");
  }

function program28(depth0,data) {
  
  
  data.buffer.push("\n                        <span class=\"flaticon solid megaphone-1\"></span>\n                        Post an Update\n                    ");
  }

  data.buffer.push("<div class=\"l-wrapper\">\n        \n            <nav class=\"manage-project-sidebar\">\n                <h4><span class=\"flaticon solid notebook-1\"></span> Project Story </h4>\n                <ul class=\"manage-project-nav\">\n                    <li>\n                        ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectPlan.basics", options) : helperMissing.call(depth0, "linkTo", "myProjectPlan.basics", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                    </li>\n                    <li>\n                        ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectPlan.description", options) : helperMissing.call(depth0, "linkTo", "myProjectPlan.description", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                    </li>\n                    <li>\n                        ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectPlan.location", options) : helperMissing.call(depth0, "linkTo", "myProjectPlan.location", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                    </li>\n                    <li>\n                        ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectPlan.media", options) : helperMissing.call(depth0, "linkTo", "myProjectPlan.media", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                    </li>\n                </ul>\n                \n                <h4><span class=\"flaticon solid briefcase-1\"></span> Organisation</h4>\n                <ul class=\"manage-project-nav\">\n                    <li>\n                        ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(9, program9, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectPlan.organisation", options) : helperMissing.call(depth0, "linkTo", "myProjectPlan.organisation", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                    </li>\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "organization", {hash:{},inverse:self.noop,fn:self.program(11, program11, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "needsFunding", {hash:{},inverse:self.noop,fn:self.program(16, program16, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                \n                ");
  hashContexts = {'class': depth0};
  hashTypes = {'class': "STRING"};
  options = {hash:{
    'class': ("btn btn-iconed btn-primary btn-submit")
  },inverse:self.noop,fn:self.program(24, program24, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectPlan.submit", options) : helperMissing.call(depth0, "linkTo", "myProjectPlan.submit", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n\n            </nav>\n\n            <form class=\"l-content\">\n                ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "outlet", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n            </form>\n            \n            <div class=\"toolbox\">\n                <h3 class=\"toolbox-title\">\n                    <em class=\"flaticon solid wrench-1\"></em>\n                    Crowdsourcing\n                </h3>\n                <div class=\"toolbox-content\">\n                    <p>Do you need someone to help writing your business plan?</p>\n                    ");
  hashContexts = {'name': depth0,'class': depth0};
  hashTypes = {'name': "STRING",'class': "STRING"};
  options = {hash:{
    'name': ("button"),
    'class': ("btn btn-iconed")
  },inverse:self.noop,fn:self.program(26, program26, data),contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "projectTaskNew", "getProject", options) : helperMissing.call(depth0, "linkTo", "projectTaskNew", "getProject", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                </div>\n            </div>\n\n            <div class=\"toolbox\">\n                <h3 class=\"toolbox-title\">\n                    <em class=\"flaticon solid megaphone-1\"></em>\n                    Project Updates\n                </h3>\n                <div class=\"toolbox-content\">\n                    <p>Why not? Ask the crowd for feedback on your idea!</p>\n                    ");
  hashContexts = {'tagName': depth0,'class': depth0};
  hashTypes = {'tagName': "STRING",'class': "STRING"};
  options = {hash:{
    'tagName': ("button"),
    'class': ("btn btn-iconed")
  },inverse:self.noop,fn:self.program(28, program28, data),contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "project", "getProject", options) : helperMissing.call(depth0, "linkTo", "project", "getProject", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                </div>\n            </div>\n\n        </div>");
  return buffer;
  
});Ember.TEMPLATES['my_project_plan_ambassadors'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n\n                <li class=\"control-group has-popover\" data-content=\"Email address of the amabassador\">\n                    <label class=\"control-label\">Name</label>\n                    <div class=\"controls\">\n                        ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("ambassador.name"),
    'classBinding': ("ambassador.errors.name.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    </div>\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "ambassador.errors.name", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n                </li>\n\n                <li class=\"control-group has-popover\" data-content=\"Email address of the amabassador\">\n                    <label class=\"control-label\">Email</label>\n                    <div class=\"controls\">\n                        ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("ambassador.email"),
    'classBinding': ("ambassador.errors.email.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    </div>\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "ambassador.errors.email", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n                </li>\n\n                <li class=\"control-group has-popover\" data-content=\"Can you tell something more about this ambassador.\">\n                    <label class=\"control-label\">Description</label>\n                    <div class=\"controls\">\n                        ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextArea", {hash:{
    'valueBinding': ("ambassador.description"),
    'classBinding': ("ambassador.errors.description.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    </div>\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "ambassador.errors.description", {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n                </li>\n\n                <li class=\"control-group wide has-popover\" data-content=\"Do you want to remove this ambassador?\">\n                    <label class=\"control-label wide\">\n                        <a><span class=\"flaticon solid minus-2\"></span> Remove this ambassador</a>\n                    </label>\n                    <hr>\n                </li>\n            ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "ambassador.errors.name", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                    ");
  return buffer;
  }
function program3(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program5(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "ambassador.errors.email", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                    ");
  return buffer;
  }

function program7(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "ambassador.errors.description", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                    ");
  return buffer;
  }

  data.buffer.push("<legend>\n        <strong>Ambassadors</strong>\n        <p>\n            \nAn ambassador is somebody who can tell something about your smart idea or about you as a person or your organisation. Ambassadors will make your story more credible and will add that little something extra. You probably have lots of people in your network who can act as ambassador, but be sure it is not your mom and the person meets our criteria (see <a href=\"/#!/pages/faq-projects\">FAQ</a>).<br><br>\nDo you want to start a crowdfunding campaign? Make sure all ambassadors create a 1%Profile and post a short comment on your project page to promote your smart idea.<br><br>\nYou've to have at least 3 ambassadors. (more? great!)<br><br>\n            \n        </p>\n    </legend>\n\n    <fieldset>\n        <ul>\n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "ambassador", "in", "ambassadors", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            <li class=\"control-group wide has-popover\" data-content=\"You should at least add three ambassadors.\">\n                <label class=\"control-label wide\">\n                    <a><span class=\"flaticon solid plus-2\"></span> Add another ambassador</a>\n                </label>\n            </li>\n        </ul>\n    </fieldset>\n\n    <button><span class=\"flaticon solid right-2\"></span>Save & Next</button>");
  return buffer;
  
});Ember.TEMPLATES['my_project_plan_approved'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, self=this, helperMissing=helpers.helperMissing;

function program1(depth0,data) {
  
  
  data.buffer.push("Campaign");
  }

  data.buffer.push("<div class=\"l-wrapper \">\n        <article class=\"l-content\">\n            <header class=\"page-header\">\n                <h2>Yeah! Your plan has been approved.</h2>\n                <p>You can start your  ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectCampaign", options) : helperMissing.call(depth0, "linkTo", "myProjectCampaign", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("</p>\n            </header>\n        </article>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['my_project_plan_bank'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n        <fieldset>\n            <ul>\n                <li class=\"control-group has-popover\" data-content=\"Name of the bank that holds your acount.\">\n                    <label class=\"control-label\">Account bank name</label>\n                    <div class=\"controls\">\n                        ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("organization.account_bank_name"),
    'classBinding': ("organization.errors.account_bank_name.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    </div>\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization.errors.account_bank_name", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </li>\n\n                <li class=\"control-group has-popover\" data-content=\"Address of the bank.\">\n                    <label class=\"control-label\">Bank address</label>\n                    <div class=\"controls\">\n                        ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("organization.account_bank_address"),
    'classBinding': ("organization.errors.account_bank_address.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    </div>\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization.errors.account_bank_address", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </li>\n\n                <li class=\"control-group has-popover\" data-content=\"Country of the bank.\">\n                    <label class=\"control-label\">Bank country</label>\n                    <div class=\"controls\">\n                        ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.CountrySelectView", {hash:{
    'valueBinding': ("organization.account_bank_country"),
    'classBinding': ("organization.errors.account_bank_country.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    </div>\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization.errors.account_bank_country", {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </li>\n\n                <li class=\"control-group has-popover\" data-content=\"Bank account number.\">\n                    <label class=\"control-label\">Account number</label>\n                    <div class=\"controls\">\n                        ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("organization.account_number"),
    'classBinding': ("organization.errors.account_number.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    </div>\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization.errors.account_number", {hash:{},inverse:self.noop,fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </li>\n\n                <li class=\"control-group has-popover\" data-content=\"Name of the bank account holder.\">\n                    <label class=\"control-label\">Account name</label>\n                    <div class=\"controls\">\n                        ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("organization.account_name"),
    'classBinding': ("organization.errors.account_name.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    </div>\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization.errors.account_name", {hash:{},inverse:self.noop,fn:self.program(11, program11, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </li>\n\n                <li class=\"control-group has-popover\" data-content=\"Account holder city\">\n                    <label class=\"control-label\">Account city</label>\n                    <div class=\"controls\">\n                        ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("organization.account_city"),
    'classBinding': ("organization.errors.account_city.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    </div>\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization.errors.account_city", {hash:{},inverse:self.noop,fn:self.program(13, program13, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </li>\n\n                <li class=\"control-group has-popover\" data-content=\"You ony have to enter this if your country supports IBAN.\">\n                    <label class=\"control-label\">Account IBAN</label>\n                    <div class=\"controls\">\n                        ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("organization.account_iban"),
    'classBinding': ("organization.errors.account_iban.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    </div>\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization.errors.account_iban", {hash:{},inverse:self.noop,fn:self.program(15, program15, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </li>\n\n                <li class=\"control-group has-popover\" data-content=\"BIC/SWIFT code for your bank\">\n                    <label class=\"control-label\">Bank BIC/SWIFT code</label>\n                    <div class=\"controls\">\n                        ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("organization.account_bic"),
    'classBinding': ("organization.errors.account_bic.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    </div>\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization.errors.account_bic", {hash:{},inverse:self.noop,fn:self.program(17, program17, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </li>\n\n                <li class=\"control-group has-popover\" data-content=\"Do we need more information to make an eventual bank transfer?\">\n                    <label class=\"control-label\">Extra info</label>\n                    <div class=\"controls\">\n                        ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextArea", {hash:{
    'valueBinding': ("organization.account_other"),
    'classBinding': ("organization.errors.account_other.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    </div>\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization.errors.account_other", {hash:{},inverse:self.noop,fn:self.program(19, program19, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </li>\n            </ul>\n        </fieldset>\n        <button><span class=\"flaticon solid right-2\"></span>Save & Next</button>\n\n    ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "organization.errors.account_bank_name", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                    ");
  return buffer;
  }
function program3(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program5(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "organization.errors.account_bank_address", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                    ");
  return buffer;
  }

function program7(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "organization.errors.account_bank_country", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                    ");
  return buffer;
  }

function program9(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "organization.errors.account_number", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                    ");
  return buffer;
  }

function program11(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "organization.errors.account_name", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                    ");
  return buffer;
  }

function program13(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "organization.errors.account_city", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                    ");
  return buffer;
  }

function program15(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "organization.errors.account_iban", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                    ");
  return buffer;
  }

function program17(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "organization.errors.account_bic", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                    ");
  return buffer;
  }

function program19(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "organization.errors.account_other", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                    ");
  return buffer;
  }

function program21(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization", {hash:{},inverse:self.program(24, program24, data),fn:self.program(22, program22, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    ");
  return buffer;
  }
function program22(depth0,data) {
  
  
  data.buffer.push("\n            Loading data\n        ");
  }

function program24(depth0,data) {
  
  
  data.buffer.push("\n            You should create an organisation profile first.\n        ");
  }

  data.buffer.push("<legend>\n        <strong>Bank details</strong>\n    </legend>\n\n    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization.isLoaded", {hash:{},inverse:self.program(21, program21, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  return buffer;
  
});Ember.TEMPLATES['my_project_plan_basics'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.title", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program4(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.pitch", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }

function program6(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.theme", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }

function program8(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.tags", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }

function program10(depth0,data) {
  
  var buffer = '', hashContexts, hashTypes;
  data.buffer.push("\n                        <label class=\"radio\">");
  hashContexts = {'value': depth0};
  hashTypes = {'value': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': ("skills")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("<span>Skills and expertise</span></label>\n                        <label class=\"radio\">");
  hashContexts = {'value': depth0};
  hashTypes = {'value': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': ("finance")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("<span>Crowdfunding campaign</span></label>\n                        <label class=\"radio\">");
  hashContexts = {'value': depth0};
  hashTypes = {'value': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': ("both")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("<span>Both</span></label>\n                    ");
  return buffer;
  }

  data.buffer.push("<legend>\n        <strong>Project basics</strong>\n    </legend>\n\n    <fieldset>\n        <ul>\n            <li class=\"control-group has-popover\" data-content=\"Be short, creative, simple and memorable.\">\n                <label class=\"control-label\">Title</label>\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("title"),
    'placeholder': ("Title"),
    'classBinding': ("errors.title.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.title", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n\n            <li class=\"control-group has-popover\" data-content=\"Pitch your smart idea in one sentence.\">\n                <label class=\"control-label\">Pitch</label>\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextArea", {hash:{
    'valueBinding': ("pitch"),
    'placeholder': ("Description"),
    'classBinding': ("errors.pitch.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.pitch", {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n        </ul>\n    </fieldset>\n    <fieldset>\n        <ul>\n            <li class=\"control-group has-popover\" data-content=\"Select one of the themes.\">\n                <label class=\"control-label\">Theme</label>\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.ThemeSelectView", {hash:{
    'valueBinding': ("theme"),
    'classBinding': ("errors.theme.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.theme", {hash:{},inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n        </ul>\n    </fieldset>\n    \n    <fieldset>\n        <ul>\n            <li class=\"control-group\">\n                <label class=\"control-label\">\n                    Tags (");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "tags.length", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(")<br>\n                    <small>Between 2 and 5 tags</small>\n                </label>\n                <div class=\"controls\">\n                    ");
  hashContexts = {'tagsBinding': depth0,'classBinding': depth0};
  hashTypes = {'tagsBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.TagWidget", {hash:{
    'tagsBinding': ("tags"),
    'classBinding': ("errors.tags.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.tags", {hash:{},inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n        </ul>\n    </fieldset>\n    <fieldset>\n        <ul>\n            <li class=\"control-group has-popover\" data-content=\"What do you need to realise your smart idea?\">\n                <label class=\"control-label\">\n                    What do you need?\n                </label>\n\n                <div class=\"controls\">\n                    ");
  hashContexts = {'name': depth0,'selectedValueBinding': depth0,'class': depth0};
  hashTypes = {'name': "STRING",'selectedValueBinding': "STRING",'class': "STRING"};
  stack1 = helpers.view.call(depth0, "Em.RadioButtonGroup", {hash:{
    'name': ("need"),
    'selectedValueBinding': ("need"),
    'class': ("radio-group")
  },inverse:self.noop,fn:self.program(10, program10, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </div>\n            </li>\n\n        </ul>\n    </fieldset>\n\n    <button><span class=\"flaticon solid right-2\"></span>Save & Next</button>");
  return buffer;
  
});Ember.TEMPLATES['my_project_plan_budget'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', hashContexts, hashTypes;
  data.buffer.push("\n                <li class=\"control-group\">\n                    <div class=\"controls wide budget-line\">\n                        <a>\n                            <span class=\"flaticon solid minus-2\"></span>\n                        </a>\n                        ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'class': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'class': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("line.description"),
    'placeholder': ("Description"),
    'class': ("description")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'class': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'class': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("line.amount"),
    'placeholder': ("Amount euro"),
    'class': ("amount")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    </div>\n                </li>\n            ");
  return buffer;
  }

function program3(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.unless.call(depth0, "validBudget", {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                ");
  return buffer;
  }
function program4(depth0,data) {
  
  
  data.buffer.push("\n                        <div class=\"has-errors\"><p>Total budget shouldn't be over 5000 euro.</p></div>\n                    ");
  }

function program6(depth0,data) {
  
  
  data.buffer.push("\n                    <div class=\"has-errors\"><p>Start adding items to your budget.</p></div>\n                ");
  }

  data.buffer.push("<legend>\n        <strong>Budget needed</strong>\n        <p>\n\nTime to let us know how the money that you will be raising will be spent! Be sure to give us a\ndetailed insight in your budget as it will only make your credibility go up. Just one little suggestion\nbefore you start; be realistic in your crowdfunding goal. Better a smaller amount and make it then a\nlarge amount and have nothing in the end. Also, there are certain things not allowed to ask money for.\nCheck them in our <a href=\"/#!/pages/faq-projects\">FAQ</a>.\n<br>\nPlease add 5% administration fee to your budget. The total amount, including the fee, cannot exceed 5.000 Euro.\n\n        </p>\n    </legend>\n\n    <fieldset>\n        <ul>\n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "line", "in", "budgetLines", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            <li class=\"control-group\">\n                <div class=\"controls wide budget\">\n                    <a>\n                        <span class=\"flaticon solid plus-2\"></span>\n                        Add an item to your needed budget.\n                    </a>\n                </div>\n            </li>\n            <li class=\"control-group\">\n                <div class=\"controls wide budget\">\n                    <div class=\"budget-description\">Total budget needed:</div>\n                    <div class=\"budget-amount\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "totalBudget", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</div>\n                </div>\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "totalBudget", {hash:{},inverse:self.program(6, program6, data),fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n            </li>\n        </ul>\n    </fieldset>\n\n    <button><span class=\"flaticon solid right-2\"></span>Save & Next</button>");
  return buffer;
  
});Ember.TEMPLATES['my_project_plan_campaign'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.moneyNeeded", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program4(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.campaign", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }

  data.buffer.push("<legend>\n        <strong>Crowndfunding Campaign</strong>\n        <p>\n            \nSometimes people are lucky and support for their project directly comes in from all corners of the world. However, for the other 99% it starts with their own network and their networks’ network. This basically means you have to tell your network about your project on 1%Club. Once, twice, maybe even three times. Per e-mail, on Facebook, on Twitter, face-to-face, by phone, by poster or in a video message. Whatever you need to do to get them on board! Our advice would be to have some people on board to help you do this.<br><br>\nDo realize that you have to put in work to make it work. And remember, hard work tends to pays off. You have 6 months for this campaign so use it wisely. If you don’t succeed the money will go back to the people who gave it and they will choose another project.<br><br>\nNeed more tips and tricks? Read our <a href=\"/#!/pages/faq-projects\">FAQ</a>.<br><br>\n            \n\n        </p>\n    </legend>\n\n    <fieldset>\n        <ul>\n            <li class=\"control-group has-popover\" data-content=\"Describe in one sentence where the money is needed for.\">\n                <label class=\"control-label\">Money needed for</label>\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("moneyNeeded"),
    'classBinding': ("errors.moneyNeeded.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.moneyNeeded", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n\n            <li class=\"control-group has-popover\" data-content=\"What is your crowdfunding strategy? What steps are you going to take? \">\n                <label class=\"control-label\">Campaign strategy</label>\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'rows': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'rows': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextArea", {hash:{
    'valueBinding': ("campaign"),
    'rows': ("6"),
    'classBinding': ("errors.campaign.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.campaign", {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n        </ul>\n    </fieldset>\n\n    <button><span class=\"flaticon solid right-2\"></span>Save & Next</button>");
  return buffer;
  
});Ember.TEMPLATES['my_project_plan_description'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.description", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program4(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.effects", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }

function program6(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.future", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }

function program8(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.forWho", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }

function program10(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.reach", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }

  data.buffer.push("<legend>\n        <strong>Project description</strong>\n    </legend>\n\n    <fieldset>\n        <ul>\n            <li class=\"control-group has-popover\" data-content=\"Blow us away with the details!\">\n                <label class=\"control-label\">Why, what and how</label>\n                <div class=\"controls wide\">\n                    ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0,'rows': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING",'rows': "INTEGER"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextArea", {hash:{
    'valueBinding': ("description"),
    'classBinding': ("errors.description.length:error"),
    'rows': (12)
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.description", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n\n            <li class=\"control-group has-popover\" data-content=\"What will be the Impact? How will your Smart Idea change the lives of people?\">\n                <label class=\"control-label\">Effects</label>\n                <div class=\"controls wide\">\n                    ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0,'rows': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING",'rows': "INTEGER"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextArea", {hash:{
    'valueBinding': ("effects"),
    'classBinding': ("errors.effects.length:error"),
    'rows': (6)
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.effects", {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n\n            <li class=\"control-group has-popover\" data-content=\"How will this project be self-sufficient and sustainable in the long term?\">\n                <label class=\"control-label\">Future</label>\n                <div class=\"controls wide\">\n                    ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0,'rows': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING",'rows': "INTEGER"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextArea", {hash:{
    'valueBinding': ("future"),
    'classBinding': ("errors.future.length:error"),
    'rows': (6)
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.future", {hash:{},inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n        </ul>\n    </fieldset>\n    <fieldset>\n        <ul>\n            <li class=\"control-group has-popover\" data-content=\"Describe your target group.\">\n                <label class=\"control-label\">For who</label>\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextArea", {hash:{
    'valueBinding': ("forWho"),
    'classBinding': ("errors.forWho.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.forWho", {hash:{},inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n\n            <li class=\"control-group has-popover\" data-content=\"How many people do you expect to reach? Enter a number (e.g. 50)\">\n                <label class=\"control-label\">People reached</label>\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("reach"),
    'classBinding': ("errors.reach.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.reach", {hash:{},inverse:self.noop,fn:self.program(10, program10, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n        </ul>\n    </fieldset>\n\n    <button><span class=\"flaticon solid right-2\"></span>Save & Next</button>");
  return buffer;
  
});Ember.TEMPLATES['my_project_plan_index'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, escapeExpression=this.escapeExpression, self=this, helperMissing=helpers.helperMissing;

function program1(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n        <fieldset>\n            <legend>\n                <strong>Project Coach</strong>\n            </legend>\n            <div class=\"fieldset-content\">\n                <p>Meet <strong>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.coach.first_name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong>, who's ready to guide you through writing your ProjectPlan.\n                    <br>\n                    <a>\n                        <figure class=\"member-avatar\"><img></figure>\n                        <strong class=\"member-name\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.coach.full_name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong>\n                    </a>\n                </p>\n            </div>\n        </fieldset>\n    ");
  return buffer;
  }

function program3(depth0,data) {
  
  
  data.buffer.push("<em class=\"flaticon solid right-2\"></em>Next");
  }

  data.buffer.push("<fieldset>\n        <legend>\n            <strong>Woohoo, your pitch was accepted!</strong>\n        </legend>\n        <div class=\"fieldset-content\">\n            <p>To complete your project plan, please fill in the empty spaces. Are there still some gaps? Don’t worry! We have a community full of people that are willing to help you. The only thing you need to do is create a 1%Skills task ask for the right expertise.</p>\n        </div>\n    </fieldset>\n\n    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "project.coach", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n    ");
  hashContexts = {'class': depth0};
  hashTypes = {'class': "STRING"};
  options = {hash:{
    'class': ("btn btn-iconed btn-next")
  },inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "myProjectPlan.basics", options) : helperMissing.call(depth0, "linkTo", "myProjectPlan.basics", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  return buffer;
  
});Ember.TEMPLATES['my_project_plan_legal'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "organization.errors.legalStatus", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program4(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                        <a><span class=\"flaticon solid minus-2\"></span></a>\n                        <a>\n                            ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "doc.file.name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" <small>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "doc.file.size", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</small><br>\n                        </a>\n                    ");
  return buffer;
  }

  data.buffer.push("<legend>\n        <strong>Legal status</strong>\n        <p>Please upload an excerpt of your official registration to show that your NGO is registered.</p>\n    </legend>\n\n\n    <fieldset>\n        <ul>\n            <li class=\"control-group has-popover\" data-content=\"What is the legal status of your organization? Include the registration number.\">\n                <label class=\"control-label\">Legal status</label>\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("organization.legalStatus"),
    'placeholder': ("Legal status"),
    'classBinding': ("organization.errors.legalStatus.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization.errors.legalStatus", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n\n            <li class=\"control-group has-popover\" data-content=\"please upload a copy of your passport. Make sure it's a valid one and we can read it clearly!\">\n                <label class=\"control-label\">\n                    Documents (");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "organization.documents.length", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(")<br>\n                    <small>\n                        .jpg, .png or .pdf\n                    </small>\n                </label>\n\n                <div class=\"controls manage-project-files\">\n                    <a class=\"btn btn-iconed btn-upload\">\n                        ");
  hashContexts = {'valueBinding': depth0,'name': depth0,'multiple': depth0};
  hashTypes = {'valueBinding': "STRING",'name': "STRING",'multiple': "BOOLEAN"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.UploadMultipleFiles", {hash:{
    'valueBinding': ("image"),
    'name': ("documents"),
    'multiple': (true)
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        <span class=\"flaticon solid upload-document-1\"></span>\n                        Upload scan(s)\n                    </a>\n                    <br>\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "doc", "in", "organization.documents", {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </div>\n            </li>\n        </ul>\n    </fieldset>\n\n    <button><span class=\"flaticon solid right-2\"></span>Save & Next</button>");
  return buffer;
  
});Ember.TEMPLATES['my_project_plan_media'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  
  data.buffer.push("\n                            <img>\n                        ");
  }

function program3(depth0,data) {
  
  
  data.buffer.push("\n                            <img src=\"images/empty.png\">\n                        ");
  }

  data.buffer.push("<legend>\n        <strong>Project media</strong>\n        <p>Upload a photo</p>\n    </legend>\n    \n    <fieldset>\n        <ul>\n            <li class=\"control-group has-popover\" data-content=\"This photo will represent your idea on 1%Club. So make sure it's personal, unique and recognisable for your smart idea and that it looks nice too!\">\n                <label class=\"control-label\">\n                    Project Picture\n                </label>\n\n                <div class=\"controls manage-project-image\">\n                    <a class=\"btn btn-iconed btn-upload\">\n                        ");
  hashContexts = {'fileBinding': depth0,'name': depth0,'accept': depth0,'id': depth0};
  hashTypes = {'fileBinding': "STRING",'name': "STRING",'accept': "STRING",'id': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.UploadFile", {hash:{
    'fileBinding': ("image"),
    'name': ("image"),
    'accept': ("image/*"),
    'id': ("image")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        <span class=\"flaticon solid upload-document-1\"></span>\n                        Upload picture\n                    </a>\n                    <br>\n                    <div>\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "image", {hash:{},inverse:self.program(3, program3, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </div>\n                </div>\n            </li>\n        </ul>\n    </fieldset>\n    <button><span class=\"flaticon solid right-2\"></span>Save & Next</button>");
  return buffer;
  
});Ember.TEMPLATES['my_project_plan_organisation'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n        <fieldset>\n            <ul>\n                <li class=\"control-group has-popover\" data-content=\"Name of your organisation\">\n                    <label class=\"control-label\">Name</label>\n                    <div class=\"controls\">\n                        ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("organization.name"),
    'classBinding': ("organization.errors.name.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    </div>\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization.errors.name", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </li>\n\n                <li class=\"control-group has-popover\" data-content=\"Describe your organisation\">\n                    <label class=\"control-label\">Description</label>\n                    <div class=\"controls\">\n                        ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextArea", {hash:{
    'valueBinding': ("organization.description"),
    'classBinding': ("organization.errors.description.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    </div>\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization.errors.description", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </li>\n            </ul>\n        </fieldset>\n        <fieldset>\n            <legend>\n                <strong>Address</strong>\n            </legend>\n            <ul>\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "address", "in", "organization.addresses", {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                <li class=\"control-group has-popover\" data-content=\"Does your organisation has more addresses?\">\n                    <label class=\"control-label\">\n                        <a><span class=\"flaticon solid plus-2\"></span> Add address</a>\n                    </label>\n                </li>\n            </ul>\n        </fieldset>\n        <fieldset>\n            <legend>\n                <strong>Online</strong>\n            </legend>\n            <ul>\n\n                <li class=\"control-group has-popover\" data-content=\"Does your organization have a website?\">\n                    <label class=\"control-label\">Website</label>\n                    <div class=\"controls\">\n                        ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("organization.website"),
    'classBinding': ("organization.errors.website.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    </div>\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization.errors.website", {hash:{},inverse:self.noop,fn:self.program(20, program20, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </li>\n\n                <li class=\"control-group has-popover\" data-content=\"Email address\">\n                    <label class=\"control-label\">Email</label>\n                    <div class=\"controls\">\n                        ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("organization.email"),
    'classBinding': ("organization.errors.email.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    </div>\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization.errors.email", {hash:{},inverse:self.noop,fn:self.program(22, program22, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </li>\n\n                <li class=\"control-group has-popover\" data-content=\"Does your organization have a twitter account?\">\n                    <label class=\"control-label\">Twitter</label>\n                    <div class=\"controls\">\n                        ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("organization.twitter"),
    'placeholder': ("@twitteraccount"),
    'classBinding': ("organization.errors.twitter.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    </div>\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization.errors.twitter", {hash:{},inverse:self.noop,fn:self.program(24, program24, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </li>\n\n                <li class=\"control-group has-popover\" data-content=\"Does your organization have a facebook group?\">\n                    <label class=\"control-label\">Facebook</label>\n                    <div class=\"controls\">\n                        ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("organization.facebook"),
    'placeholder': ("https://www.facebook.com/<groupname>"),
    'classBinding': ("organization.errors.facebook.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    </div>\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization.errors.facebook", {hash:{},inverse:self.noop,fn:self.program(26, program26, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </li>\n\n                <li class=\"control-group has-popover\" data-content=\"Can we reach you on Skype?\">\n                    <label class=\"control-label\">Skype</label>\n                    <div class=\"controls\">\n                        ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("organization.skype"),
    'placeholder': ("skype name"),
    'classBinding': ("organization.errors.skype.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    </div>\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization.errors.skype", {hash:{},inverse:self.noop,fn:self.program(28, program28, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </li>\n            </ul>\n        </fieldset>\n        <button><span class=\"flaticon solid right-2\"></span>Save & Next</button>\n    ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "organization.errors.name", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                    ");
  return buffer;
  }
function program3(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program5(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "organization.errors.description", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                    ");
  return buffer;
  }

function program7(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n\n                    <li class=\"control-group has-popover\" data-content=\"What type of address is this? You can add multiple addresses\">\n                        <label class=\"control-label\">Type</label>\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.AddressTypeSelectView", {hash:{
    'valueBinding': ("address.type"),
    'classBinding': ("address.errors.type.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "address.errors.type", {hash:{},inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </li>\n\n                    <li class=\"control-group has-popover\" data-content=\"Street, house number, the place in your city\">\n                        <label class=\"control-label\">Address line 1</label>\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("address.line1"),
    'classBinding': ("address.errors.line1.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "address.errors.line1", {hash:{},inverse:self.noop,fn:self.program(10, program10, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n                    </li>\n\n                    <li class=\"control-group has-popover\" data-content=\"More about your address\">\n                        <label class=\"control-label\">Address line 2</label>\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("address.line2"),
    'classBinding': ("address.errors.line2.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "address.errors.line2", {hash:{},inverse:self.noop,fn:self.program(12, program12, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </li>\n\n\n                    <li class=\"control-group has-popover\" data-content=\"City or village..\">\n                        <label class=\"control-label\">City</label>\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("address.city"),
    'classBinding': ("address.errors.city.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "address.errors.city", {hash:{},inverse:self.noop,fn:self.program(14, program14, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </li>\n\n                    <li class=\"control-group has-popover\" data-content=\"Postal code\">\n                        <label class=\"control-label\">Postal code</label>\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("address.postal_code"),
    'classBinding': ("address.errors.postal_code.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "address.errors.postal_code", {hash:{},inverse:self.noop,fn:self.program(16, program16, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </li>\n\n                    <li class=\"control-group has-popover\" data-content=\"Country or territory\">\n                        <label class=\"control-label\">Country</label>\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.CountrySelectView", {hash:{
    'valueBinding': ("address.country"),
    'classBinding': ("address.errors.country.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "address.errors.country", {hash:{},inverse:self.noop,fn:self.program(18, program18, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </li>\n\n                    <li class=\"control-group has-popover\" data-content=\"Do you want to remove this address?\">\n                        <label class=\"control-label wide\">\n                            <a><span class=\"flaticon solid minus-2\"></span> Remove this address</a>\n                        </label>\n                        <hr>\n                    </li>\n                ");
  return buffer;
  }
function program8(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "address.errors.type", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                        ");
  return buffer;
  }

function program10(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "address.errors.line1", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                        ");
  return buffer;
  }

function program12(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "address.errors.line2", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                        ");
  return buffer;
  }

function program14(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "address.errors.city", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                        ");
  return buffer;
  }

function program16(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "address.errors.postal_code", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                        ");
  return buffer;
  }

function program18(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "address.errors.country", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                        ");
  return buffer;
  }

function program20(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "organization.errors.website", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                    ");
  return buffer;
  }

function program22(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "organization.errors.email", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                    ");
  return buffer;
  }

function program24(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "organization.errors.twitter", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                    ");
  return buffer;
  }

function program26(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "organization.errors.facebook", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                    ");
  return buffer;
  }

function program28(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "organization.errors.skype", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                    ");
  return buffer;
  }

function program30(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n        <fieldset>\n            <ul>\n                <li class=\"control-group has-popover\" data-content=\"Choose your organisation from the list or create a new one.\">\n                    <label class=\"control-label\">Organisation</label>\n                    <div class=\"controls\">\n                        <ul>\n                            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "organizations", {hash:{},inverse:self.noop,fn:self.program(31, program31, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                            <li>\n                                <h4>create new</h4>\n                                Create a new organization to run this project.\n                                <br>\n                                <a><span class=\"flaticon solid plus-2\"> Create</a>\n                            </li>\n                        </ul>\n                    </div>\n                </li>\n            </ul>\n        </fieldset>\n    ");
  return buffer;
  }
function program31(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                                <li>\n                                    <h4>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</h4>\n                                    ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "description", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                                    <br>\n                                    <a><span class=\"flaticon solid plus-2\"> Select</a>\n                                </li>\n                            ");
  return buffer;
  }

  data.buffer.push("<legend>\n        <strong>Organisation</strong>\n    </legend>\n\n    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization", {hash:{},inverse:self.program(30, program30, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  return buffer;
  
});Ember.TEMPLATES['my_project_plan_rejected'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  


  data.buffer.push("<div class=\"l-wrapper\">\n        <article class=\"l-content\">\n            <header class=\"page-header\">\n                <h2>We're sorry, your plan has been rejected.</h2>\n                <p>Please contact us if you need support to define your smart idea.</p>\n            </header>\n        </article>\n    </div>");
  
});Ember.TEMPLATES['my_project_plan_review'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  


  data.buffer.push("<div class=\"l-wrapper\">\n        <article class=\"l-content\">\n            <header class=\"page-header\">\n                <h2>Your plan is in review now</h2>\n                <p>We'll get back to you soon!</p>\n            </header>\n        </article>\n    </div>");
  
});Ember.TEMPLATES['my_project_plan_submit'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  
  data.buffer.push("\n        <button><span class=\"flaticon solid right-2\"></span>Submit plan</button>\n    ");
  }

  data.buffer.push("<legend>\n        <strong>Submit Plan</strong>\n    </legend>\n    \n    <fieldset>\n    \n        <div class=\"fieldset-content\">\n            \n            <h3>Check!</h3>\n            \n                Make sure that you filled out the entire form and that all items to the left have a <span class=\"flaticon solid checkmark-2\"></span> check sign.\n                If one of the items still shows a circle then that still needs some work.\n            \n        </div>\n        \n        <ul>\n            <li class=\"control-group has-popover\" data-content=\"Agree to the terms to submit the plan\">\n                <div class=\"controls wide\">\n                    <label class=\"checkbox wide\">");
  hashContexts = {'checkedBinding': depth0,'classBinding': depth0};
  hashTypes = {'checkedBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.Checkbox", {hash:{
    'checkedBinding': ("agreed"),
    'classBinding': ("errors.agreed.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" <span>I agree to the  <a>general terms and conditions</a></span></label>\n                </div>\n            </li>\n        </ul>\n    </fieldset>\n    \n    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "agreed", {hash:{},inverse:self.program(1, program1, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  return buffer;
  
});Ember.TEMPLATES['news'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, helperMissing=helpers.helperMissing, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts, options;
  data.buffer.push("\n	                    <li>\n	                        <a>\n	                            <strong class=\"blog-title\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong> <em class=\"blog-timestamp\">");
  hashContexts = {'formatting': depth0};
  hashTypes = {'formatting': "STRING"};
  options = {hash:{
    'formatting': ("X")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "publicationDate", options) : helperMissing.call(depth0, "localize", "publicationDate", options))));
  data.buffer.push("</em>\n	                        </a>\n	                    </li>\n	                ");
  return buffer;
  }

function program3(depth0,data) {
  
  
  data.buffer.push("\n		                <a>\n		                    <span class=\"flaticon solid left-circle-2\"></span>\n		                    previous 5\n		                </a>\n		            ");
  }

function program5(depth0,data) {
  
  
  data.buffer.push("\n		                <a>\n		                    next 5\n		                    <span class=\"flaticon solid right-circle-2\"></span>\n		                </a>\n		            ");
  }

  data.buffer.push("<div class=\"l-section\" id=\"news\">\n    <section class=\"l-wrapper\">\n    \n	        <article class=\"l-content\">\n	            ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "outlet", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	        </article>\n    	\n	        <sidebar class=\"l-sidebar page-nav\">\n	        \n                <h3>More news</h3>\n	            <ul>\n	                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "model", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	            </ul>\n	            \n	            <div class=\"page-pagination\">\n		            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "controller.hasPrevious", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n		            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "controller.hasNext", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	            </div>\n	            \n	        </sidebar>\n    	</div>\n    </section>\n</div>");
  return buffer;
  
});Ember.TEMPLATES['news_index'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  


  data.buffer.push("Loading the latest news");
  
});Ember.TEMPLATES['news_item'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, escapeExpression=this.escapeExpression, helperMissing=helpers.helperMissing;


  data.buffer.push("<header class=\"l-page-header\">\n        <a ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.action.call(depth0, "openInBigBox", "userModal", "author", {hash:{},contexts:[depth0,depth0,depth0],types:["STRING","STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" class=\"member\">\n            <figure class=\"member-avatar\"><img ");
  hashContexts = {'src': depth0};
  hashTypes = {'src': "STRING"};
  data.buffer.push(escapeExpression(helpers.bindAttr.call(depth0, {hash:{
    'src': ("author.getAvatar")
  },contexts:[],types:[],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" alt=\"Avatar\"></figure>\n            <strong class=\"member-name\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "author.full_name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong>\n            <em class=\"timestamp\">");
  hashContexts = {'formatting': depth0};
  hashTypes = {'formatting': "STRING"};
  options = {hash:{
    'formatting': ("X")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "publicationDate", options) : helperMissing.call(depth0, "localize", "publicationDate", options))));
  data.buffer.push("</em>\n        </a>\n        <h1 class=\"page-title\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</h1>\n    </header>\n    \n    <div class=\"news-content\">\n        ");
  hashContexts = {'unescaped': depth0};
  hashTypes = {'unescaped': "STRING"};
  stack2 = helpers._triageMustache.call(depth0, "body", {hash:{
    'unescaped': ("true")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['orderThanks'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, self=this, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression;

function program1(depth0,data) {
  
  
  data.buffer.push("\n                		<p>\n						Thanks for your support! Your 1% has brought them one step closer to realise their smart idea! Don't forget to tune in to see how they're doing! \n					</p>\n					");
  }

function program3(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n                		<p>\n						Thanks for your support! We'd be happy to keep you posted on the progress of the project(s) you supported. Why? Because it's a fun and personal way to see what's happening with your 1%. Sounds good? Just become a 1%Member!\n					</p>\n					<p>");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "signup", options) : helperMissing.call(depth0, "linkTo", "signup", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("</p>\n					");
  return buffer;
  }
function program4(depth0,data) {
  
  
  data.buffer.push("Become a 1%Member <em class=\"flaticon solid right-angle-quote-1\"></em>");
  }

function program6(depth0,data) {
  
  
  data.buffer.push("\n                        <h3>You just supported these projects</h3>\n                    ");
  }

function program8(depth0,data) {
  
  
  data.buffer.push("\n                        <h3>You just supported this project</h3>\n                    ");
  }

function program10(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts, options;
  data.buffer.push("\n                        ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.partial || depth0.partial),stack1 ? stack1.call(depth0, "thanksDonation", options) : helperMissing.call(depth0, "partial", "thanksDonation", options))));
  data.buffer.push("\n	                ");
  return buffer;
  }

function program12(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                <h3>Your donation is set</h3>\n        		<p>\n				Your donation will be deducted from your account.\n				</p>\n				<p>Donation total: <strong>&euro; ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "total", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(",-</strong></p>\n				");
  return buffer;
  }

  data.buffer.push("<div id=\"thanks\">\n	<div class=\"l-section\">\n        <section class=\"l-wrapper\">\n        \n            <div class=\"l-content\">    	\n            	<figure>\n        			<img src=\"/static/assets/images/you-made-it-work.png\" alt=\"You made it work\"  />\n				</figure>\n            	\n            	<header>\n                	<h1>Donation Successful!</h1>\n					");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "controllers.currentUser.isAuthenticated", {hash:{},inverse:self.program(3, program3, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            	</header>\n            \n            </div>\n        </div>\n    </div>\n\n    <div class=\"l-section\">\n        <section class=\"l-wrapper\">\n			<div class=\"l-content\">\n			\n				<header>\n                	");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "moreThanOneDonation", {hash:{},inverse:self.program(8, program8, data),fn:self.program(6, program6, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </header>\n	\n	            <ul class=\"project-list\">\n	                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "donation", "in", "donations", {hash:{},inverse:self.noop,fn:self.program(10, program10, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	            </ul>\n            </div>\n            \n            <sidebar class=\"l-sidebar\">\n            	");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "recurring", {hash:{},inverse:self.noop,fn:self.program(12, program12, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </sidebar>\n        </section>\n    </div>\n</div>");
  return buffer;
  
});Ember.TEMPLATES['page'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, self=this, helperMissing=helpers.helperMissing;

function program1(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n        	<section class=\"l-wrapper\">\n					<article class=\"l-content\">\n						<header class=\"page-header\">\n		                	<h1>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</h1>\n						</header>\n						");
  hashContexts = {'unescaped': depth0};
  hashTypes = {'unescaped': "STRING"};
  stack1 = helpers._triageMustache.call(depth0, "body", {hash:{
    'unescaped': ("true")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push(" \n					</article>\n					\n					<sidebar class=\"l-sidebar page-nav\">\n						<h3>About 1%Club</h3>\n						<ul>\n							<li><a>Our Story</a></li>\n							<li><a>Frequently Asked Questions</a></li>\n							<li><a>Meet the team</a></li>\n							<li><a>Partners</a></li>\n							<li><a>Press</a></li>\n							<li><a>Work at 1%Club</a></li>\n							<li>");
  hashContexts = {'href': depth0};
  hashTypes = {'href': "BOOLEAN"};
  options = {hash:{
    'href': (true)
  },inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "contactMessage", options) : helperMissing.call(depth0, "linkTo", "contactMessage", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("</a></li>\n						</ul>\n					</sidebar>\n					\n        		</div>\n        	</section>\n        ");
  return buffer;
  }
function program2(depth0,data) {
  
  
  data.buffer.push("Contact");
  }

function program4(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n        	");
  hashContexts = {'unescaped': depth0};
  hashTypes = {'unescaped': "STRING"};
  stack1 = helpers._triageMustache.call(depth0, "body", {hash:{
    'unescaped': ("true")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n        ");
  return buffer;
  }

  data.buffer.push("<div class=\"l-section\"id=\"page\" >\n        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "view.showTitle", {hash:{},inverse:self.program(4, program4, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['partner'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashContexts, hashTypes, options, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts, options;
  data.buffer.push("\n                    ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.render || depth0.render),stack1 ? stack1.call(depth0, "projectPreview", "project", options) : helperMissing.call(depth0, "render", "projectPreview", "project", options))));
  data.buffer.push("\n                ");
  return buffer;
  }

function program3(depth0,data) {
  
  
  data.buffer.push("\n                    <li class=\"no-results\">No projects found.</li>\n                ");
  }

  data.buffer.push("<div class=\"l-section\" id=\"partner-detail\">\n        <section class=\"l-wrapper\">\n        \n            <figure class=\"image\">\n                <img ");
  hashContexts = {'src': depth0};
  hashTypes = {'src': "STRING"};
  data.buffer.push(escapeExpression(helpers.bindAttr.call(depth0, {hash:{
    'src': ("image.large")
  },contexts:[],types:[],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("  />\n            </figure>\n            \n            <article>\n                <h1>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</h1>\n                <p>");
  hashContexts = {'formatting': depth0};
  hashTypes = {'formatting': "STRING"};
  options = {hash:{
    'formatting': ("br")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.linebreaks || depth0.linebreaks),stack1 ? stack1.call(depth0, "description", options) : helperMissing.call(depth0, "linebreaks", "description", options))));
  data.buffer.push("</p>\n            </article>\n            \n        </section>\n\n        <section class=\"l-wrapper\">\n            <ul id=\"search-results\">\n                ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers.each.call(depth0, "project", "in", "projects", {hash:{},inverse:self.program(3, program3, data),fn:self.program(1, program1, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n            </ul>\n        </section>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['password_reset'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.new_password1", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program4(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.new_password2", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            ");
  return buffer;
  }
function program5(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"alert alert-error\">\n                        ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    </div>\n                ");
  return buffer;
  }

  data.buffer.push("<div class=\"modal\">\n    <div class=\"modal-header\">\n        <h3>Reset your password</h3>\n    </div>\n\n    <div class=\"modal-body\">\n        <form>\n            <div class=\"control-group\">\n                <div class=\"control-label\">New password</div>\n\n                <div class=\"controls\">\n                    ");
  hashContexts = {'type': depth0,'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'type': "STRING",'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'type': ("password"),
    'valueBinding': ("new_password1"),
    'classBinding': ("errors.new_password1.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.new_password1", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </div>\n\n            <div class=\"control-group\">\n                <div class=\"control-label\">Confirm new password</div>\n\n                <div class=\"controls\">\n                    ");
  hashContexts = {'type': depth0,'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'type': "STRING",'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'type': ("password"),
    'valueBinding': ("new_password2"),
    'classBinding': ("errors.new_password2.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n            </div>\n\n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.new_password2", {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n        </form>\n    </div>\n\n    <div class=\"modal-footer\">\n        <button class=\"btn btn-iconed right\">\n            <em class=\"flaticon solid checkmark-1\"></em>\n            Reset password\n        </button>\n    </div>\n</div>\n\n<div class=\"modal-backdrop\"></div>");
  return buffer;
  
});Ember.TEMPLATES['paymentProfile'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n        <a ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.action.call(depth0, "openInBox", "login", {hash:{},contexts:[depth0,depth0],types:["ID","STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" class=\"btn-login\"><span class=\"flaticon solid lock-1\"></span> <strong>Have an account?</strong><br> Log in here</a>\n    ");
  return buffer;
  }

function program3(depth0,data) {
  
  
  data.buffer.push("\n        		<strong>Great your doing another donation!</strong>\n    			<p>To process your donation, please check if your information is still correct.</p>\n        	");
  }

function program5(depth0,data) {
  
  
  data.buffer.push("\n    			<strong>Please to meet you</strong>\n    			<p>To process your donation we need some information.</p>\n        	");
  }

function program7(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n	            <ul>\n	                <li class=\"control-group\">\n	                    <label class=\"control-label\">Your full name</label>\n	                    <div class=\"controls\">\n	                        ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'class': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'class': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("firstName"),
    'placeholder': ("First name"),
    'class': ("inline-prepend"),
    'classBinding': ("errors.first_name.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                        ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'class': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'class': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("lastName"),
    'placeholder': ("Last name"),
    'class': ("inline-append"),
    'classBinding': ("errors.last_name.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                    </div>\n	                </li>\n	\n	                <li class=\"control-group\">\n	                    <label class=\"control-label\">Email</label>\n	                    <div class=\"controls\">\n	                        ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("email"),
    'placeholder': ("Email"),
    'classBinding': ("errors.email.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                    </div>\n	\n	                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.email", {hash:{},inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                </li>\n	\n	                <li class=\"control-group\">\n	                    <label class=\"control-label\">Address</label>\n	                    <div class=\"controls\">\n	                        ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("address"),
    'placeholder': ("Address"),
    'classBinding': ("errors.address.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                    </div>\n	\n	                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.address", {hash:{},inverse:self.noop,fn:self.program(11, program11, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                </li>\n	\n	                <li class=\"control-group\">\n	                    <label class=\"control-label\">Postal code</label>\n	                    <div class=\"controls\">\n	                        ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("postalCode"),
    'placeholder': ("Postal code"),
    'classBinding': ("errors.postal_code.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                    </div>\n	\n	                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.postal_code", {hash:{},inverse:self.noop,fn:self.program(13, program13, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                </li>\n	\n	                <li class=\"control-group\">\n	                    <label class=\"control-label\">City</label>\n	                    <div class=\"controls\">\n	                        ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("city"),
    'placeholder': ("City"),
    'classBinding': ("errors.city.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                    </div>\n	\n	                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.city", {hash:{},inverse:self.noop,fn:self.program(15, program15, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                </li>\n	\n	                <li class=\"control-group\">\n	                    <label class=\"control-label\">Country</label>\n	                    <div class=\"controls\">\n	                        ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.CountryCodeSelectView", {hash:{
    'valueBinding': ("country"),
    'placeholder': ("Country"),
    'classBinding': ("errors.country.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                    </div>\n	                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.country", {hash:{},inverse:self.noop,fn:self.program(17, program17, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                </li>\n	            </ul>\n	        ");
  return buffer;
  }
function program8(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.email", {hash:{},inverse:self.noop,fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                    ");
  return buffer;
  }
function program9(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program11(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.address", {hash:{},inverse:self.noop,fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                    ");
  return buffer;
  }

function program13(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.postal_code", {hash:{},inverse:self.noop,fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                    ");
  return buffer;
  }

function program15(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.city", {hash:{},inverse:self.noop,fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                    ");
  return buffer;
  }

function program17(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.country", {hash:{},inverse:self.noop,fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                    ");
  return buffer;
  }

function program19(depth0,data) {
  
  
  data.buffer.push("\n	        <button class=\"btn btn-primary btn-iconed btn-next\"><span class=\"flaticon solid right-2\"></span>Next Step</button>\n	    ");
  }

function program21(depth0,data) {
  
  
  data.buffer.push("\n	        <button disabled=\"disabled\" class=\"btn btn-iconed btn-next\"><span class=\"flaticon solid right-2\"></span>Next Step</button>\n	    ");
  }

function program23(depth0,data) {
  
  
  data.buffer.push("\n        <p>\"You're about to make a big impact! Did you know that every 1%Project has 6 months to reach its target? And, if the target isn't reached you will be able to support another project with this donation. If this is the case, you'll receive an email from us explaining the next steps.</p>\n    ");
  }

function program25(depth0,data) {
  
  
  data.buffer.push("\n        <p>You're about to make a big impact! Did you know that every 1%Project has 6 months to reach its target? And, if the target isn't reached we'll make sure your donation will support a similar project.</p>\n    ");
  }

  data.buffer.push("<div class=\"l-content\">\n    \n    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.unless.call(depth0, "controllers.currentUser.isAuthenticated", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    \n	<form>\n    	<legend>\n        	");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "controllers.currentUser.isAuthenticated", {hash:{},inverse:self.program(5, program5, data),fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    	</legend>\n	    	\n	    <fieldset>\n	    	\n	        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "model.isLoaded", {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	    </fieldset>\n	\n	    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isComplete", {hash:{},inverse:self.program(21, program21, data),fn:self.program(19, program19, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	\n	</form>\n</div>\n\n<div class=\"l-sidebar\">\n\n    <h3>Did you know?</h3>\n    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "controllers.currentUser.isAuthenticated", {hash:{},inverse:self.program(25, program25, data),fn:self.program(23, program23, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n</div>");
  return buffer;
  
});Ember.TEMPLATES['paymentSelect'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n	");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "outlet", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n");
  return buffer;
  }

function program3(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n	<div class=\"l-content fund-payment-select\">\n		<form>\n	    	<legend>\n				<strong>You're almost there!</strong>\n				<p>We'll redirect you through our payment provider where you can finish your donation securely.</p>\n			</legend>\n\n                <ul class=\"tabs tabs-vertical\">\n                    ");
  hashContexts = {'name': depth0,'selectedValueBinding': depth0,'class': depth0};
  hashTypes = {'name': "STRING",'selectedValueBinding': "STRING",'class': "STRING"};
  stack1 = helpers.view.call(depth0, "Em.RadioButtonGroup", {hash:{
    'name': ("paymentMethod"),
    'selectedValueBinding': ("redirectPaymentMethod"),
    'class': ("radio-group-tabbed")
  },inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </ul>\n                \n                <div class=\"tab-content fund-payment-type\">\n                   \n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isIdeal", {hash:{},inverse:self.program(15, program15, data),fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </div>\n            </div>\n	        \n		</form>\n	</div>\n");
  return buffer;
  }
function program4(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "redirectPaymentMethods", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    ");
  return buffer;
  }
function program5(depth0,data) {
  
  var buffer = '', hashContexts, hashTypes;
  data.buffer.push("\n                            <li class=\"tab-item\">\n                                <label class=\"tab-title radio\">");
  hashContexts = {'valueBinding': depth0};
  hashTypes = {'valueBinding': "ID"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'valueBinding': ("id")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" <span>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</span></label>\n                            </li>\n                        ");
  return buffer;
  }

function program7(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n                        <h3>Select your bank below</h3>\n                        <p>We'll redirect you through our payment provider where you can finish your donation securely.</p>\n                        <ul>\n                        ");
  hashContexts = {'name': depth0,'selectedValueBinding': depth0,'class': depth0};
  hashTypes = {'name': "STRING",'selectedValueBinding': "STRING",'class': "STRING"};
  stack1 = helpers.view.call(depth0, "Em.RadioButtonGroup", {hash:{
    'name': ("issuerId"),
    'selectedValueBinding': ("idealIssuerId"),
    'class': ("radio-group-tabbed")
  },inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                        </ul>\n                        \n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "paymentInProgress", {hash:{},inverse:self.program(13, program13, data),fn:self.program(11, program11, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            	        \n                    ");
  return buffer;
  }
function program8(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "idealIssuers", {hash:{},inverse:self.noop,fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                        ");
  return buffer;
  }
function program9(depth0,data) {
  
  var buffer = '', hashContexts, hashTypes;
  data.buffer.push("\n                                <li class=\"fund-payment-item\">\n                                    <label class=\"radio\">");
  hashContexts = {'valueBinding': depth0};
  hashTypes = {'valueBinding': "ID"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'valueBinding': ("id")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" <span>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</span></label>\n                                </li>\n                            ");
  return buffer;
  }

function program11(depth0,data) {
  
  
  data.buffer.push("\n            	            <div class=\"is-loading-small\"><img src=\"images/loading.gif\"><strong>Processing payment...</strong></div>\n            	            <button disabled=\"disabled\" class=\"btn btn-primary btn-iconed btn-submit\"><span class=\"flaticon solid right-2\"></span>Proceed with Payment</button>\n            	        ");
  }

function program13(depth0,data) {
  
  
  data.buffer.push("\n            	            <button class=\"btn btn-primary btn-iconed btn-proceed\"><span class=\"flaticon solid right-2\"></span>Proceed with Payment</button>\n            	        ");
  }

function program15(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                        <h3>You're almost there!</h3>\n                        <p>We'll redirect you through our payment provider where you can finish your donation securely.</p>\n                        \n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "paymentInProgress", {hash:{},inverse:self.program(13, program13, data),fn:self.program(11, program11, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                        \n                    ");
  return buffer;
  }

  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "controllers.currentOrder.recurring", {hash:{},inverse:self.program(3, program3, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  else { data.buffer.push(''); }
  
});Ember.TEMPLATES['paymentSignup'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var stack1, hashTypes, hashContexts, self=this, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression;

function program1(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n    <div class=\"l-content\">\n        <form>\n            <legend>\n                <strong>We'll keep you up to date!</strong>\n                <p>You already have an account. Great! We'll keep you updated with the progress of the projects you support.<br></div>\n                \n            </legend>\n        </form>\n        ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "paymentSelect", options) : helperMissing.call(depth0, "linkTo", "paymentSelect", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n    </div>\n    \n");
  return buffer;
  }
function program2(depth0,data) {
  
  
  data.buffer.push("\n            <button class=\"btn btn-primary btn-iconed btn-next\"><em class=\"flaticon solid right-2\"></em>Next</button>\n        ");
  }

function program4(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n	\n    <div class=\"l-content\">\n        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.unless.call(depth0, "controllers.currentUser.isAuthenticated", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n		\n        <form>\n                          \n			<legend>\n				<strong>Follow the progress?</strong>\n				<p>Sign up for an account and we keep you updated on the projects progress.</p>\n			</legend>\n            \n            <fieldset>  \n                <ul>\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">Your full name</label>\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'class': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'class': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("first_name"),
    'placeholder': ("First name"),
    'class': ("inline-prepend"),
    'classBinding': ("errors.first_name.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                            ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'class': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'class': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("last_name"),
    'placeholder': ("Last name"),
    'class': ("inline-append"),
    'classBinding': ("errors.last_name.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n                    </li>\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">Email</label>\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("email"),
    'classBinding': ("errors.email.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.email", {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </li>\n\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">Password</label>\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'type': depth0,'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'type': "STRING",'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'type': ("password"),
    'valueBinding': ("password"),
    'classBinding': ("errors.password.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.password", {hash:{},inverse:self.noop,fn:self.program(10, program10, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </li>\n\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">Password again</label>\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'type': depth0,'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'type': "STRING",'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'type': ("password"),
    'valueBinding': ("password2"),
    'classBinding': ("errors.password2.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.password2", {hash:{},inverse:self.noop,fn:self.program(12, program12, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </li>\n                </ul>\n                \n                <p class=\"control-group agree\">\n                    <small class=\"controls\">\n                        By joining 1%Club I hereby agree to the  \n                        <a>1%Club Terms of service</a>\n                    </small>\n                </p>\n                \n            </fieldset>\n            \n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isFormReady", {hash:{},inverse:self.program(16, program16, data),fn:self.program(14, program14, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            \n            ");
  hashContexts = {'class': depth0};
  hashTypes = {'class': "STRING"};
  options = {hash:{
    'class': ("btn-link btn-skip")
  },inverse:self.noop,fn:self.program(18, program18, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "paymentSelect", options) : helperMissing.call(depth0, "linkTo", "paymentSelect", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n\n        </form>\n    </div>\n\n    <div class=\"l-sidebar\">\n    \n    </div>\n");
  return buffer;
  }
function program5(depth0,data) {
  
  
  data.buffer.push("\n            <a><span class=\"flaticon solid lock-1\"></span> <strong>Have an account?</strong><br> Log in here</a>\n		");
  }

function program7(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.email", {hash:{},inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                        ");
  return buffer;
  }
function program8(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program10(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.password", {hash:{},inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                        ");
  return buffer;
  }

function program12(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.password2", {hash:{},inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                        ");
  return buffer;
  }

function program14(depth0,data) {
  
  
  data.buffer.push("\n                <button class=\"btn btn-primary btn-iconed btn-next\"><span class=\"flaticon solid right-2\"></span>Next Step</button>\n            ");
  }

function program16(depth0,data) {
  
  
  data.buffer.push("\n                <button disabled=\"disabled\" class=\"btn btn-iconed btn-next\"><span class=\"flaticon solid right-2\"></span>Next Step</button>\n            ");
  }

function program18(depth0,data) {
  
  
  data.buffer.push("<span class=\"flaticon solid x-1\"></span>Skip this step");
  }

  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "controllers.currentUser.isAuthenticated", {hash:{},inverse:self.program(4, program4, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  else { data.buffer.push(''); }
  
});Ember.TEMPLATES['project'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashContexts, hashTypes, options, escapeExpression=this.escapeExpression, self=this, helperMissing=helpers.helperMissing;

function program1(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<span class=\"project-location\"><span class=\"flaticon solid location-pin-1\"></span> ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "plan.country.name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</span>");
  return buffer;
  }

function program3(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<span class=\"project-theme\"><span class=\"flaticon solid tag-2\"></span> ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "plan.theme.title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</span>");
  return buffer;
  }

function program5(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts, options;
  data.buffer.push("\n            <section class=\"l-wrapper\">\n                <div class=\"project-status\">\n                    \n                	");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "campaign.deadline", {hash:{},inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n					\n					<div class=\"project-fund l-one-third\">\n                        <p class=\"project-fund-amount\">\n                            <strong class=\"amount-donated\">&euro;");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "campaign.money_donated", options) : helperMissing.call(depth0, "localize", "campaign.money_donated", options))));
  data.buffer.push("</strong>\n                            of\n                            <strong class=\"amount-asked\">&euro;");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "campaign.money_asked", options) : helperMissing.call(depth0, "localize", "campaign.money_asked", options))));
  data.buffer.push("</strong>\n                            raised\n                        </p>\n                    \n                        <div class=\"project-fund-amount-slider\"><strong style=\"width: 0%;\" class=\"slider-progress is-in-progress\"><em class=\"slider-percentage\">0%</em></strong></div>\n					</div>\n                    \n                    <div class=\"project-action l-one-third\">\n					    <a href=\"#\"><span class=\"flaticon solid wallet-1\"></span> Support project</a>\n                    </div>\n				</div>\n            </section>\n        ");
  return buffer;
  }
function program6(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"project-days-left l-one-third\">\n						<strong><span class=\"flaticon solid clock-1\"></span> ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "campaign.daysToGo", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong>\n						<em>days to go</em>\n					</div>\n					");
  return buffer;
  }

function program8(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                        <span class=\"tab-icon amount\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "wallposts.length", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</span>\n                        <strong class=\"tab-title\">\n                            Updates\n\n                            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "wallposts.length", {hash:{},inverse:self.program(14, program14, data),fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                        </strong>\n                    ");
  return buffer;
  }
function program9(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "wallposts.firstObject.isLoaded", {hash:{},inverse:self.program(12, program12, data),fn:self.program(10, program10, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                            ");
  return buffer;
  }
function program10(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes, options;
  data.buffer.push("\n                                    <em class=\"tab-subtitle\">");
  hashContexts = {'formatting': depth0};
  hashTypes = {'formatting': "STRING"};
  options = {hash:{
    'formatting': ("X")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "wallposts.firstObject.created", options) : helperMissing.call(depth0, "localize", "wallposts.firstObject.created", options))));
  data.buffer.push("</em>\n                                ");
  return buffer;
  }

function program12(depth0,data) {
  
  
  data.buffer.push("\n                                    <em class=\"tab-subtitle\">Loading&#8230;</em>\n                                ");
  }

function program14(depth0,data) {
  
  
  data.buffer.push("\n                                <em class=\"tab-subtitle\">No updates</em>\n                            ");
  }

function program16(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n                        ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(17, program17, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "projectTaskList", options) : helperMissing.call(depth0, "linkTo", "projectTaskList", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                    ");
  return buffer;
  }
function program17(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                            <span class=\"tab-icon\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "taskCount", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</span>\n                            <strong class=\"tab-title\">Tasks <em class=\"tab-subtitle\">Skills needed</em></strong>\n                        ");
  return buffer;
  }

function program19(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n                        ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(20, program20, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "projectTaskList", options) : helperMissing.call(depth0, "linkTo", "projectTaskList", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                    ");
  return buffer;
  }
function program20(depth0,data) {
  
  
  data.buffer.push("\n                            <span class=\"tab-icon\">0</span>\n                            <strong class=\"tab-title\">Tasks <em class=\"tab-subtitle\">No skills needed</em></strong>\n                        ");
  }

function program22(depth0,data) {
  
  
  data.buffer.push("\n                        <span class=\"tab-icon\"><span class=\"flaticon solid document-2\"></span></span>\n                        <strong class=\"tab-title\">Project Plan <em class=\"tab-subtitle\">Read full plan</em></strong>\n                    ");
  }

  data.buffer.push("<div class=\"l-section\" id=\"project-detail\">\n        <section class=\"l-wrapper\">\n        \n            <figure class=\"project-image l-half\">\n                <img ");
  hashContexts = {'src': depth0};
  hashTypes = {'src': "STRING"};
  data.buffer.push(escapeExpression(helpers.bindAttr.call(depth0, {hash:{
    'src': ("plan.image.large")
  },contexts:[],types:[],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" width=\"100%\" alt=\"Photo\"  />\n            </figure>\n\n            <div class=\"l-half\">\n                \n                \n                \n                <article class=\"project-info\">\n                    <div class=\"project-meta\">\n	                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "plan.country.name", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "plan.theme.title", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                </div>\n	                ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.SocialShareView", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    <h1 class=\"project-title\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "plan.title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</h1>\n                    <p class=\"project-description\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "plan.pitch", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>\n                </article>\n                \n            </div>\n        </section>\n\n        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isFundable", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    </div>\n\n    <div class=\"l-section\" id=\"project-members\">\n        <section class=\"l-wrapper\">\n            ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.ProjectMembersView", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n        </section>\n    </div>\n\n    <nav class=\"l-section\" id=\"project-actions\">\n        <div class=\"l-wrapper\">\n        \n            <ul class=\"tabs four\">\n                <li class=\"tab-updates\">\n                    ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "project.index", options) : helperMissing.call(depth0, "linkTo", "project.index", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                </li>\n                <li class=\"tab-tasks\">\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "taskCount", {hash:{},inverse:self.program(19, program19, data),fn:self.program(16, program16, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                </li>\n                <li class=\"tab-plan\">\n                    ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(22, program22, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "projectPlan", options) : helperMissing.call(depth0, "linkTo", "projectPlan", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                </li>\n            </ul>\n            \n        </div>\n    </nav>\n    ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "outlet", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  return buffer;
  
});Ember.TEMPLATES['project_list'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                <ul id=\"search-results\">\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "project", "in", "model", {hash:{},inverse:self.program(4, program4, data),fn:self.program(2, program2, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </ul>\n            ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts, options;
  data.buffer.push("\n                        ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.render || depth0.render),stack1 ? stack1.call(depth0, "projectPreview", "project", options) : helperMissing.call(depth0, "render", "projectPreview", "project", options))));
  data.buffer.push("\n                    ");
  return buffer;
  }

function program4(depth0,data) {
  
  
  data.buffer.push("\n                        <li class=\"no-results\">No projects found.</li>\n                    ");
  }

function program6(depth0,data) {
  
  
  data.buffer.push("\n                <div class=\"is-loading-big\"><img src=\"images/loading.gif\"> <strong>Loading projects</strong></div>\n            ");
  }

  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.render || depth0.render),stack1 ? stack1.call(depth0, "projectSearchForm", options) : helperMissing.call(depth0, "render", "projectSearchForm", options))));
  data.buffer.push("\n    <div class=\"l-section\">\n        <section class=\"l-wrapper\">\n            ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "model.isLoaded", {hash:{},inverse:self.program(6, program6, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n        </section>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['project_members'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  
  data.buffer.push("\n            <li class=\"project-member-coaches\">\n                <h4>Coach</h4>\n                <ul>\n                    <li>\n                        <a class=\"member\">\n                            <span class=\"member-avatar\"><img></span>\n                        </a>\n                    </li>\n                </ul>\n            </li>\n        ");
  }

function program3(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts, options;
  data.buffer.push("\n            ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.render || depth0.render),stack1 ? stack1.call(depth0, "projectSupporterList", options) : helperMissing.call(depth0, "render", "projectSupporterList", options))));
  data.buffer.push("\n        ");
  return buffer;
  }

  data.buffer.push("<ul class=\"project-member-list\">\n        <li class=\"project-member-initiator\">\n            <ul>\n                <li>\n                    <a ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.action.call(depth0, "openInBigBox", "userModal", "owner", {hash:{},contexts:[depth0,depth0,depth0],types:["STRING","STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" class=\"member\">\n                        <figure class=\"member-avatar\"><img ");
  hashContexts = {'src': depth0};
  hashTypes = {'src': "STRING"};
  data.buffer.push(escapeExpression(helpers.bindAttr.call(depth0, {hash:{
    'src': ("owner.getAvatar")
  },contexts:[],types:[],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("  /></figure>\n                        <h4>Initiator</h4>\n                        <strong class=\"member-name\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "owner.full_name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong>\n                        <em class=\"member-organisation\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "organization", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</em>\n                    </a>\n                </li>\n            </ul>\n        </li>\n\n        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "team_member", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.unless.call(depth0, "isPhasePlan", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    </ul>");
  return buffer;
  
});Ember.TEMPLATES['project_plan'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n                	<article>\n                	    <h2>Why, what and how?</h2>\n                        <p>");
  hashContexts = {'unescaped': depth0};
  hashTypes = {'unescaped': "STRING"};
  stack1 = helpers._triageMustache.call(depth0, "description", {hash:{
    'unescaped': ("true")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</p>\n    				</article>\n    			");
  return buffer;
  }

function program3(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n    				<article>\n                	    <h2>Effects</h3>\n                            <p>");
  hashContexts = {'unescaped': depth0};
  hashTypes = {'unescaped': "STRING"};
  stack1 = helpers._triageMustache.call(depth0, "effects", {hash:{
    'unescaped': ("true")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</p>\n                	</article>\n                ");
  return buffer;
  }

function program5(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n                	<article>\n                	    <h2>Future</h2>\n                        <p>");
  hashContexts = {'unescaped': depth0};
  hashTypes = {'unescaped': "STRING"};
  stack1 = helpers._triageMustache.call(depth0, "future", {hash:{
    'unescaped': ("true")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</p>\n                	</article>\n    			");
  return buffer;
  }

function program7(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n    				<article>\n                	    <h2>For who?</h2>\n                        <p>");
  hashContexts = {'unescaped': depth0};
  hashTypes = {'unescaped': "STRING"};
  stack1 = helpers._triageMustache.call(depth0, "forWho", {hash:{
    'unescaped': ("true")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</p>\n    				</article>\n    			");
  return buffer;
  }

function program9(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n    				<article>\n                	    <h2>People reached</h2>\n                        <p>");
  hashContexts = {'unescaped': depth0};
  hashTypes = {'unescaped': "STRING"};
  stack1 = helpers._triageMustache.call(depth0, "reached", {hash:{
    'unescaped': ("true")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</p>\n    				</article>\n    			");
  return buffer;
  }

function program11(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n    				<article>\n                	    <h2>Location</h3>\n    				    <p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "country.name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(", ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "country.subregion", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>\n                        <img>\n    				</article>\n    			");
  return buffer;
  }

function program13(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n    				<article>\n                	    <h2>Organisation</h2>\n    				    <h3>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "organization.name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</h3>\n                        <p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "organization.description", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>\n    				\n        				\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization.website", {hash:{},inverse:self.noop,fn:self.program(14, program14, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization.twitter", {hash:{},inverse:self.noop,fn:self.program(16, program16, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization.facebook", {hash:{},inverse:self.noop,fn:self.program(18, program18, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization.skype", {hash:{},inverse:self.noop,fn:self.program(20, program20, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                        </ul>\n    				</article>	\n                ");
  return buffer;
  }
function program14(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                            <dl>\n                                <dt><span class=\"flaticon solid link-1\"></span> Website</dt>\n                                <dd><a href=\"");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "organization.website", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "organization.website", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</a></dd>\n                            </dl>\n                        ");
  return buffer;
  }

function program16(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                            <dl>\n                                <dt><span class=\"flaticon social twitter-3\"></span> Twitter</dt>\n                                <dd><a href=\"http://twitter.com/");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "organization.twitter", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "organization.twitter", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</a></dd>\n                            </dl>\n                        ");
  return buffer;
  }

function program18(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                            <dl>\n                                <dt><span class=\"flaticon social facebook-3\"></span> Facebook</dt>\n                                <dd><a href=\"http://facebook.com/");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "organization.facebook", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "organization.facebook", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</a></dd>\n                            </dl>\n                        ");
  return buffer;
  }

function program20(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                            <dl>\n                                <dt><span class=\"flaticon social skype-2\"></span> Website</dt>\n                                <dd><a href=\"callto:");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "organization.skype", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "organization.skype", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</a></dd>\n                            </dl>\n                        ");
  return buffer;
  }

  data.buffer.push("<div class=\"l-section\" id=\"project-plan\">\n        <section class=\"l-wrapper\">\n        \n                <header>\n                	<h1>Project Plan</h1>\n                </header>\n               \n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "description", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    			\n    			");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "effects", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    			\n    			");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "future", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    				\n    			");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "forWho", {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    			\n    			");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "reached", {hash:{},inverse:self.noop,fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    \n    			");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "country.name", {hash:{},inverse:self.noop,fn:self.program(11, program11, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    			\n    			");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "organization.name", {hash:{},inverse:self.noop,fn:self.program(13, program13, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                \n        </section>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['project_preview'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n            <span class=\"project-header\">\n            \n            	<figure class=\"project-image\">\n                	<img ");
  hashContexts = {'src': depth0};
  hashTypes = {'src': "STRING"};
  data.buffer.push(escapeExpression(helpers.bindAttr.call(depth0, {hash:{
    'src': ("project.image")
  },contexts:[],types:[],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("  />\n            	</figure>\n            	\n                <span class=\"project-title\">\n                	<h3>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</h3>\n                    <span class=\"project-location\"><span class=\"flaticon solid location-pin-1\"></span> ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.country.name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</span> \n                </span>\n            </span>\n            \n	        <span>\n	            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "project.isPhasePlan", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	\n	            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "project.isPhaseCampaign", {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	\n	            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "project.isPhaseAct", {hash:{},inverse:self.noop,fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	            \n	            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "project.isPhaseResults", {hash:{},inverse:self.noop,fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	            \n	            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "project.isPhaseRealized", {hash:{},inverse:self.noop,fn:self.program(11, program11, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	        </span>\n	        \n            <span class=\"project-description\">\n                ");
  hashContexts = {'unescaped': depth0};
  hashTypes = {'unescaped': "STRING"};
  stack1 = helpers._triageMustache.call(depth0, "project.pitch", {hash:{
    'unescaped': ("true")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push(" \n                \n                <span class=\"project-view\">View project</span>\n            </span>\n	        \n        ");
  return buffer;
  }
function program2(depth0,data) {
  
  
  data.buffer.push("\n                    <span class=\"project-phase\"><span class=\"flaticon solid lightbulb-3\"></span> <strong>New</strong> <em>Smart Idea</em></span> \n	            ");
  }

function program4(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "project.campaign.money_asked", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "project.campaign.deadline", {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	            ");
  return buffer;
  }
function program5(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts, options;
  data.buffer.push("\n                        <div class=\"project-fund-amount-slider\"><strong style=\"width: 0%;\" class=\"slider-progress is-in-progress\"><em class=\"slider-percentage\">0%</em></strong></div>\n                        <span class=\"project-fund-amount\"><strong>&euro;");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "project.campaign.money_needed", options) : helperMissing.call(depth0, "localize", "project.campaign.money_needed", options))));
  data.buffer.push("</strong> <em>To go</em></span>\n                    ");
  return buffer;
  }

function program7(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                        <span class=\"project-days-left\"><span class=\"flaticon solid clock-1\"></span> <strong>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.campaign.daysToGo", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong> <em>days</em></span>\n                    ");
  return buffer;
  }

function program9(depth0,data) {
  
  
  data.buffer.push("\n                    <span class=\"project-phase\"><span class=\"flaticon solid lightbulb-3\"></span> <strong>Project funded</strong> <em>Being realized</em></span>\n	            ");
  }

function program11(depth0,data) {
  
  
  data.buffer.push("\n	                <span class=\"project-phase\"><span class=\"flaticon solid lightbulb-3\"></span> <strong>Project realized</strong> <em>See results</em></span>\n	            ");
  }

function program13(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n            <a class=\"project-tasks\"><span class=\"flaticon solid wrench-1\"></span> <strong>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.taskCount", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong> <em>task(s) available</em></a>\n        ");
  return buffer;
  }

  data.buffer.push("<li class=\"project-item\">\n    \n        ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "project", "project.getProject", options) : helperMissing.call(depth0, "linkTo", "project", "project.getProject", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n        	        \n        ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "taskCount", {hash:{},inverse:self.noop,fn:self.program(13, program13, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n    </li>");
  return buffer;
  
});Ember.TEMPLATES['project_search_form'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  
  data.buffer.push("\n		                    <a>\n		                        <span class=\"flaticon solid left-circle-2\"></span>\n		                    </a>\n		                ");
  }

function program3(depth0,data) {
  
  
  data.buffer.push("\n		                	<span class=\"previous-page\"><span class=\"flaticon solid left-circle-2\"></span></span>\n		                ");
  }

function program5(depth0,data) {
  
  
  data.buffer.push("\n		                    <a>\n		                        <span class=\"flaticon solid right-circle-2\"></span>\n		                    </a>\n		                ");
  }

function program7(depth0,data) {
  
  
  data.buffer.push("\n		                	<span class=\"next-page\"><span class=\"flaticon solid right-circle-2\"></span></span>\n		                ");
  }

  data.buffer.push("<div class=\"l-section\" id=\"search\">\n        <section class=\"l-wrapper\">\n            <form id=\"search-form\">\n                <div class=\"control\">\n                    ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("text"),
    'placeholder': ("Search")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    <span class=\"flaticon stroke zoom-2\"></span>\n                </div>\n                <div class=\"control\">\n                    ");
  hashContexts = {'valueBinding': depth0};
  hashTypes = {'valueBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.ProjectCountrySelectView", {hash:{
    'valueBinding': ("country")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    <span class=\"flaticon solid earth-1\"></span>\n                </div>\n                <div class=\"control\">\n                    ");
  hashContexts = {'valueBinding': depth0};
  hashTypes = {'valueBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.ThemeSelectView", {hash:{
    'valueBinding': ("theme")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    <span class=\"flaticon stroke tag-2\"></span>\n                </div>\n                <div class=\"control\">\n                    ");
  hashContexts = {'valueBinding': depth0};
  hashTypes = {'valueBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.ProjectPhaseSelectView", {hash:{
    'valueBinding': ("phase")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                    <span class=\"flaticon stroke flag-1\"></span>\n                </div>\n            </form>\n        </section>\n    </div>\n\n    <div class=\"l-section\">\n        <section class=\"l-wrapper\">\n            <article id=\"search-navigation\">\n            	\n            	<header>\n                	<h2>Results <em>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "controllers.projectList.model.meta.total", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</em></h2>\n                    <a>\n                        <span class=\"flaticon solid x-2\"></span> Reset Search Filter\n                    </a>\n            	</header>\n                \n                <div class=\"search-sort\">\n                    Sort:\n                    <a>Most popular</a>\n                    \n                    <a>Newest</a>\n                    <a>Almost funded</a>\n                    <a>Near deadline</a>\n                </div>\n                \n                <div class=\"search-pagination\">\n                	<span class=\"search-showing\">Showing ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "rangeStart", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("-");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "rangeEnd", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</span>\n                	<span class=\"search-pages-control\">\n		                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "hasPreviousPage", {hash:{},inverse:self.program(3, program3, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n		                \n		                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "hasNextPage", {hash:{},inverse:self.program(7, program7, data),fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                	</span>\n                </div>\n                \n            </article>\n        </section>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['project_supporter'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n        <a class=\"member\" ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.action.call(depth0, "openInBigBox", "userModal", "supporter.member", {hash:{},contexts:[depth0,depth0,depth0],types:["STRING","STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" ");
  hashContexts = {'data-title': depth0,'data-content': depth0};
  hashTypes = {'data-title': "STRING",'data-content': "STRING"};
  data.buffer.push(escapeExpression(helpers.bindAttr.call(depth0, {hash:{
    'data-title': ("supporter.member.full_name"),
    'data-content': ("supporter.time_since")
  },contexts:[],types:[],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(">\n            <span class=\"member-avatar\"><img ");
  hashContexts = {'src': depth0};
  hashTypes = {'src': "STRING"};
  data.buffer.push(escapeExpression(helpers.bindAttr.call(depth0, {hash:{
    'src': ("supporter.member.getAvatar")
  },contexts:[],types:[],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("  alt=\"supporter.member.full_name\"  /></span>\n        </a>\n    ");
  return buffer;
  }

function program3(depth0,data) {
  
  
  data.buffer.push("\n        <a class=\"member\" data-title=\"guest\">\n            <span class=\"member-avatar\"><img src=\"/static/assets/images/default-avatar.png\" alt=\"Guest\"></span>\n        </a>\n    ");
  }

  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "supporter.member", {hash:{},inverse:self.program(3, program3, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  else { data.buffer.push(''); }
  
});Ember.TEMPLATES['project_supporter_list'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n        <li class=\"project-member-supporters\">\n            <ul>\n                <li class=\"project-member-supporters-total\">\n                    <strong>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "supporters.length", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong>\n                    <br>\n                    <em>Total</em>\n                </li>\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "supporter", "in", "controller", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </ul>\n            <h4>Supporters</h4>\n        </li>\n    ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                    ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.ProjectSupporterView", {hash:{},contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                ");
  return buffer;
  }

  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "supporters.length", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  else { data.buffer.push(''); }
  
});Ember.TEMPLATES['project_task_list'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, self=this, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression;

function program1(depth0,data) {
  
  var buffer = '', stack1, stack2, hashContexts, hashTypes, options;
  data.buffer.push("\n            <div class=\"owner-actions\">\n            	\n            	<header>\n            		<h3>You're the project owner</h3>\n					<p>You can add a new task.</p>\n            	</header>\n            	\n	            ");
  hashContexts = {'class': depth0};
  hashTypes = {'class': "STRING"};
  options = {hash:{
    'class': ("btn btn-primary btn-iconed task-add")
  },inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "projectTaskNew", options) : helperMissing.call(depth0, "linkTo", "projectTaskNew", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n            </div>\n			");
  return buffer;
  }
function program2(depth0,data) {
  
  
  data.buffer.push("\n	                <span class=\"flaticon solid plus-1\"></span>\n	                Add a task\n	            ");
  }

function program4(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts, options;
  data.buffer.push("\n                    ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0,depth0],types:["ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.render || depth0.render),stack1 ? stack1.call(depth0, "projectTaskPreview", "task", options) : helperMissing.call(depth0, "render", "projectTaskPreview", "task", options))));
  data.buffer.push("\n                ");
  return buffer;
  }

function program6(depth0,data) {
  
  
  data.buffer.push("\n                    <li class=\"no-results\">No tasks currently available for this project.</li>\n                ");
  }

  data.buffer.push("<div class=\"l-section\">\n        <section class=\"l-wrapper\">\n			\n			");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isProjectOwner", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n			\n            <ul id=\"search-results\">\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "task", "in", "controller", {hash:{},inverse:self.program(6, program6, data),fn:self.program(4, program4, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </ul>\n            \n        </section>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['project_task_preview'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n    	\n    	    <h2 class=\"task-category\"><span class=\"flaticon solid wrench-1\"></span> ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "task.skill.name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</h2>\n    	\n    	    <span class=\"task-header\">\n                <span class=\"task-image\">\n                	<img>\n            	</span>\n                <span class=\"task-title\">\n                	<h3>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "task.title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</h3>\n                	<h4>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</h4> \n                </span>\n            </span>\n            \n	        <div class=\"task-status\">\n	            <ul class=\"task-meta\">\n	                <li>\n	                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "task.isStatusOpen", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "task.isStatusInProgress", {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "task.isStatusClosed", {hash:{},inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "task.isStatusRealized", {hash:{},inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	\n	                </li>\n	                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.unless.call(depth0, "task.isStatusRealized", {hash:{},inverse:self.noop,fn:self.program(10, program10, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                <li>\n	                    <span class=\"flaticon solid watch-1\"></span>\n	                    ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "task.timeNeeded", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                </li>\n	                <li>\n	                	<span class=\"flaticon solid location-pin-1\"></span>\n	                	");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.country.name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                </li>\n	            </ul>\n	        </div>\n	        \n	        <div class=\"task-description\">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam sed aliquam lacus, at luctus lacus. Pellentesque pellentesque nibh ac lacus mollis, nec fringilla nunc pharetra. Suspendisse et metus at lacus interdum pharetra ac aliquet libero. Donec dignissim et nunc vel gravida.</div>\n	        \n    	");
  return buffer;
  }
function program2(depth0,data) {
  
  
  data.buffer.push("\n	                        <span class=\"flaticon solid clipboard-1\"></span>\n	                        Open\n	                    ");
  }

function program4(depth0,data) {
  
  
  data.buffer.push("\n	                        <span class=\"flaticon solid upload-to-clipboard-1\"></span>\n	                        In progress\n	                    ");
  }

function program6(depth0,data) {
  
  
  data.buffer.push("\n	                        <span class=\"flaticon solid delete-from-clipboard-1\"></span>\n	                        Closed\n	                    ");
  }

function program8(depth0,data) {
  
  
  data.buffer.push("\n	                        <span class=\"flaticon solid clipboard-checkmark-1\"></span>\n	                        Realised\n	                    ");
  }

function program10(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes, options;
  data.buffer.push("\n	                <li>\n	                	<span class=\"flaticon solid calendar-1\"></span>\n	                    ");
  hashContexts = {'formatting': depth0};
  hashTypes = {'formatting': "STRING"};
  options = {hash:{
    'formatting': ("X")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "task.deadline", options) : helperMissing.call(depth0, "localize", "task.deadline", options))));
  data.buffer.push("\n	                </li>\n	                ");
  return buffer;
  }

  data.buffer.push("<li class=\"task-item\">\n    	");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "projectTask", "task", options) : helperMissing.call(depth0, "linkTo", "projectTask", "task", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n    </li>");
  return buffer;
  
});Ember.TEMPLATES['project_wallpost'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, options, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes, options;
  data.buffer.push("\n                    <em class=\"timestamp\">");
  hashContexts = {'formatting': depth0};
  hashTypes = {'formatting': "STRING"};
  options = {hash:{
    'formatting': ("X")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "created", options) : helperMissing.call(depth0, "localize", "created", options))));
  data.buffer.push("</em>\n                ");
  return buffer;
  }

function program3(depth0,data) {
  
  
  data.buffer.push("\n                    <a>Delete</a>\n                ");
  }

function program5(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                <h3 class=\"wallpost-title\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</h3>\n            ");
  return buffer;
  }

function program7(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n                <div class=\"video\">");
  hashContexts = {'unescaped': depth0};
  hashTypes = {'unescaped': "STRING"};
  stack1 = helpers._triageMustache.call(depth0, "video_html", {hash:{
    'unescaped': ("true")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n            ");
  return buffer;
  }

function program9(depth0,data) {
  
  
  data.buffer.push("\n                <ul class=\"photo-viewer\">\n                    <li class=\"photo\"><img></li>\n                </ul>\n            ");
  }

function program11(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                <ul class=\"photo-viewer\">\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "photo", "in", "photos", {hash:{},inverse:self.noop,fn:self.program(12, program12, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </ul>\n            ");
  return buffer;
  }
function program12(depth0,data) {
  
  
  data.buffer.push("\n                        <li class=\"photo\"><a><img></a></li>\n                    ");
  }

  data.buffer.push("<article class=\"wallpost\">\n    \n        <header class=\"wallpost-header\">\n        \n            <div class=\"wallpost-member\">\n                <a ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.action.call(depth0, "openInBigBox", "userModal", "author", {hash:{},contexts:[depth0,depth0,depth0],types:["ID","STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" class=\"member\">\n                    <span class=\"member-avatar\">\n                        <img ");
  hashContexts = {'src': depth0};
  hashTypes = {'src': "STRING"};
  data.buffer.push(escapeExpression(helpers.bindAttr.call(depth0, {hash:{
    'src': ("author.getAvatar")
  },contexts:[],types:[],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" alt=\"");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "author.full_name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\"  />\n                    </span>\n                    <strong class=\"member-name\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "author.full_name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong>\n                </a>\n            </div>\n            \n            <div class=\"wallpost-meta\">\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "created", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isAuthor", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </div>\n        </header>\n\n        <div class=\"wallpost-content\">            \n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "title", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            \n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "video_html", {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n            <div class=\"text\">");
  hashContexts = {'unescaped': depth0};
  hashTypes = {'unescaped': "STRING"};
  stack1 = helpers._triageMustache.call(depth0, "text", {hash:{
    'unescaped': ("true")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n\n            \n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "photo", {hash:{},inverse:self.noop,fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "photos.length", {hash:{},inverse:self.noop,fn:self.program(11, program11, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n	    </div>\n        \n        <div class=\"wallpost-reactions\">\n            ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.render || depth0.render),stack1 ? stack1.call(depth0, "wallpostReactionList", "reactions", options) : helperMissing.call(depth0, "render", "wallpostReactionList", "reactions", options))));
  data.buffer.push("\n        </div>\n\n    </article>");
  return buffer;
  
});Ember.TEMPLATES['project_wallpost_list'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, options, escapeExpression=this.escapeExpression, self=this, helperMissing=helpers.helperMissing;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n    	            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "item.isLoaded", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    	        ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "item.isSystemWallpost", {hash:{},inverse:self.program(5, program5, data),fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    	            ");
  return buffer;
  }
function program3(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n        	                ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.SystemWallpostView", {hash:{},contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        ");
  return buffer;
  }

function program5(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n        	                ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.ProjectWallpostView", {hash:{},contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        ");
  return buffer;
  }

function program7(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                    <a ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.action.call(depth0, "showMore", {hash:{},contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" class=\"btn-link btn-more\">\n                        <span class=\"flaticon solid plus-2\"></span> Show more <small>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "remainingItemCount", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" more</small>\n                    </a>\n                ");
  return buffer;
  }

  data.buffer.push("<div id=\"l-section\">\n        <section class=\"l-wrapper\">\n        	<div class=\"l-content\" id=\"wallposts\">\n    \n    	        ");
  hashContexts = {'itemController': depth0};
  hashTypes = {'itemController': "STRING"};
  stack1 = helpers.each.call(depth0, "item", "in", "items", {hash:{
    'itemController': ("wallpost")
  },inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            	\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "canLoadMore", {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    \n        	</div>\n    \n            <sidebar class=\"l-sidebar\">\n            	");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.render || depth0.render),stack1 ? stack1.call(depth0, "projectWallpostNew", options) : helperMissing.call(depth0, "render", "projectWallpostNew", options))));
  data.buffer.push("\n            </sidebar>\n            \n        </section>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['project_wallpost_new'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, self=this, helperMissing=helpers.helperMissing;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isProjectOwner", {hash:{},inverse:self.program(4, program4, data),fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', hashContexts, hashTypes;
  data.buffer.push("\n        	<h3>Write an update</h3>\n        	<p>Write an update of your project to inform your crowd.</p>\n            ");
  hashContexts = {'content': depth0};
  hashTypes = {'content': "ID"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.MediaWallpostNewView", {hash:{
    'content': ("content")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n        ");
  return buffer;
  }

function program4(depth0,data) {
  
  var buffer = '', hashContexts, hashTypes;
  data.buffer.push("\n        	<h3>Write a comment</h3>\n        	<p>Write an comment to place on the project's wall.</p>\n            ");
  hashContexts = {'content': depth0};
  hashTypes = {'content': "ID"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.TextWallpostNewView", {hash:{
    'content': ("content")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n        ");
  return buffer;
  }

function program6(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n    	<h3>Write a comment</h3>\n    	<a>Login</a> or become a ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "signup", options) : helperMissing.call(depth0, "linkTo", "signup", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push(" to leave a comment.</p>\n    ");
  return buffer;
  }
function program7(depth0,data) {
  
  
  data.buffer.push("member");
  }

  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "controllers.currentUser.isAuthenticated", {hash:{},inverse:self.program(6, program6, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  else { data.buffer.push(''); }
  
});Ember.TEMPLATES['recurringDirectDebitPayment'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.name", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program4(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.city", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                ");
  return buffer;
  }

function program6(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.account", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                ");
  return buffer;
  }

function program8(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "paymentInProgress", {hash:{},inverse:self.program(11, program11, data),fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	    ");
  return buffer;
  }
function program9(depth0,data) {
  
  
  data.buffer.push("\n		        <span class=\"is-loading-small\"><img src=\"images/loading.gif\"><em>Updating monthly donation ...</em></span>\n		        <button disabled=\"disabled\" class=\"btn btn-primary btn-iconed btn-submit\"><span class=\"flaticon solid right-2\"></span>Submit</button>\n	        ");
  }

function program11(depth0,data) {
  
  
  data.buffer.push("\n	            <button class=\"btn btn-primary btn-iconed btn-submit\"><span class=\"flaticon solid right-2\"></span>Submit</button>\n	        ");
  }

function program13(depth0,data) {
  
  
  data.buffer.push("\n	        <button disabled=\"disabled\" class=\"btn btn-iconed btn-submit\"><span class=\"flaticon solid right-2\"></span>Submit</button>\n	    ");
  }

  data.buffer.push("<div class=\"l-content\">\n	<form>\n	    <fieldset>\n	    	    \n    		<legend>\n    	    	<strong>You're almost there!</strong>\n    	        <p>Add or edit your bank account information and submit to set your monthly donations.</p>\n    	    </legend>\n	    \n	        <ul>\n	            <li class=\"control-group\">\n	                <label class=\"control-label\">Account Name</label>\n	                <div class=\"controls\">\n	                    ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("name"),
    'placeholder': ("Full name as it appears on your bank account"),
    'classBinding': ("errors.name.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                </div>\n	                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.name", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	            </li>\n	\n	            <li class=\"control-group\">\n	                <label class=\"control-label\">Account City</label>\n	                <div class=\"controls\">\n	                    ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("city"),
    'placeholder': ("City registered on your bank account"),
    'classBinding': ("errors.city.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                </div>\n	                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.city", {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	            </li>\n	\n	            <li class=\"control-group\">\n	                <label class=\"control-label\">Account Number</label>\n	                <div class=\"controls\">\n	                    ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("account"),
    'placeholder': ("Your bank account number"),
    'classBinding': ("errors.account.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                </div>\n	                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.account", {hash:{},inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	            </li>\n	        </ul>\n	        \n	        <p class=\"control-group agree\">\n                <small class=\"controls\">\n                    By clicking submit, I authorize 1%Club to withdraw money every month.\n                </small>\n            </p>\n	        \n	    </fieldset>\n	\n	    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isFormReady", {hash:{},inverse:self.program(13, program13, data),fn:self.program(8, program8, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	\n	</form>\n</div>\n	\n<div class=\"l-sidebar\">\n	<h3>Your monthly donation</h3>\n	<p>Thank you 1%Friend! You're about to set your monthly donation amount to &euro; ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "controllers.currentOrderDonationList.recurringTotal", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>\n</div>");
  return buffer;
  
});Ember.TEMPLATES['recurringOrderThanks'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, self=this, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                	\n                	<figure>\n                		<img src=\"/static/assets/images/you-made-it-work.png\" alt=\"You made it work\"  />\n                	</figure>\n                	\n                	<header>\n	                	<h1>Donation Successful!</h1>\n						");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "controllers.currentUser.isAuthenticated", {hash:{},inverse:self.program(4, program4, data),fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	            	</header>\n            	\n                ");
  return buffer;
  }
function program2(depth0,data) {
  
  
  data.buffer.push("\n	                		<p>\n							Thanks for your support! Your 1% has brought them one step closer to realise their smart idea! Don't forget to tune in to see how they're doing! \n						</p>\n						");
  }

function program4(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n	                		<p>\n							Thanks for your support! We'd be happy to keep you posted on the progress of the project(s) you supported. Why? Because it's a fun and personal way to see what's happening with your 1%. Sounds good? Just become a 1%Member!\n						</p>\n						<p>");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "signup", options) : helperMissing.call(depth0, "linkTo", "signup", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("</p>\n						");
  return buffer;
  }
function program5(depth0,data) {
  
  
  data.buffer.push("Become a 1%Member <em class=\"flaticon solid right-angle-quote-1\"></em>");
  }

function program7(depth0,data) {
  
  var buffer = '', stack1, stack2, hashContexts, hashTypes, options;
  data.buffer.push("\n                	<header>\n                    	<h1>No donation set...</h1>\n						");
  hashContexts = {'class': depth0};
  hashTypes = {'class': "STRING"};
  options = {hash:{
    'class': ("edit-monthly-donations")
  },inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "currentOrder.donationList", options) : helperMissing.call(depth0, "linkTo", "currentOrder.donationList", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                	</header>\n                ");
  return buffer;
  }
function program8(depth0,data) {
  
  
  data.buffer.push("\n                        	<strong>Create or enable your monthly donation</strong>\n						");
  }

function program10(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n\n                   <header>\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "donations", {hash:{},inverse:self.program(16, program16, data),fn:self.program(11, program11, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                   </header>\n\n                    <ul class=\"project-list\">\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "donation", "in", "donations", {hash:{},inverse:self.noop,fn:self.program(18, program18, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                            \n                            \n                        \n                    </ul>\n                ");
  return buffer;
  }
function program11(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "moreThanOneDonation", {hash:{},inverse:self.program(14, program14, data),fn:self.program(12, program12, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                        ");
  return buffer;
  }
function program12(depth0,data) {
  
  
  data.buffer.push("\n                                <h3>You just supported these projects</h3>\n                            ");
  }

function program14(depth0,data) {
  
  
  data.buffer.push("\n                                <h3>You just supported this project</h3>\n                            ");
  }

function program16(depth0,data) {
  
  
  data.buffer.push("\n                            <h3>You just supported the top three projects.</h3>\n                        ");
  }

function program18(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts, options;
  data.buffer.push("\n                            ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.partial || depth0.partial),stack1 ? stack1.call(depth0, "thanksDonation", options) : helperMissing.call(depth0, "partial", "thanksDonation", options))));
  data.buffer.push("\n                        ");
  return buffer;
  }

function program20(depth0,data) {
  
  
  data.buffer.push("\n                	<p>Your monthly donation will be deducted from your account at the beginning of each month.</p>\n                ");
  }

  data.buffer.push("<div id=\"thanks\">\n    <div class=\"l-section\">\n        <section class=\"l-wrapper\">\n            <div class=\"l-content\">\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "recurringPayment.active", {hash:{},inverse:self.program(7, program7, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </div>\n        </section>\n    </div>\n\n    <div class=\"l-section\">\n        <section class=\"l-wrapper\">\n			<div class=\"l-content\">\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "recurringPayment.active", {hash:{},inverse:self.noop,fn:self.program(10, program10, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </div>\n            \n            <sidebar class=\"l-sidebar\">\n            	\n            	<h3>Your monthly donation is set</h3>\n				");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "donations.length", {hash:{},inverse:self.noop,fn:self.program(20, program20, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n				<p>Monthly donation total: <strong>&euro; ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "recurringPayment.amount", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(",-</strong></p>\n				\n            	\n                \n            </sidebar>\n        </section>\n    </div>\n</div>");
  return buffer;
  
});Ember.TEMPLATES['request_password_reset'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', hashTypes, hashContexts, escapeExpression=this.escapeExpression;


  data.buffer.push("<div class=\"modal\">\n        <div class=\"modal-header\">\n            <a class=\"close\" rel=\"close\">&times;</a>\n            <h3>Forgot your password?</h3>\n        </div>\n\n        <div class=\"modal-body\">\n        	<form>\n	            <p>Enter your email address and we'll send you an email so you can set a new password.</p>\n	            <div class=\"control-group\">\n	                <div class=\"alert alert-error hidden\" id=\"passwordResetError\">\n	                    ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "error", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                </div>\n	            </div>\n	            <div class=\"control-group\">\n	                <div class=\"control-label\">Email address</div>\n	                <div class=\"controls\">\n	                    <input id=\"passwordResetEmail\" type=\"text\">\n	                </div>\n	            </div>\n        	</form>\n        </div>\n\n        <div class=\"modal-footer\">\n            <a href=\"#\" class=\"btn btn-iconed btn-secondary\" rel=\"secondary\">\n                <em class=\"flaticon solid checkmark-1\"></em>\n                Reset password\n            </a>\n        </div>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['signup'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, options, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression;


  data.buffer.push("<div id=\"signup\" class=\"page\">\n	<section class=\"l-wrapper\">\n	    <article class=\"l-content\">\n	        ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.partial || depth0.partial),stack1 ? stack1.call(depth0, "signup_content", options) : helperMissing.call(depth0, "partial", "signup_content", options))));
  data.buffer.push("\n	    </article>\n	    \n	    <sidebar class=\"l-sidebar\">\n	    	");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.partial || depth0.partial),stack1 ? stack1.call(depth0, "signup_sidebar", options) : helperMissing.call(depth0, "partial", "signup_sidebar", options))));
  data.buffer.push("\n		</sidebar>\n	</section>\n</div>");
  return buffer;
  
});Ember.TEMPLATES['system_wallpost'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, options, escapeExpression=this.escapeExpression, helperMissing=helpers.helperMissing, self=this;

function program1(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                <a>\n                    <strong class=\"member-name\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "author.full_name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong>\n                </a>\n                ");
  return buffer;
  }

function program3(depth0,data) {
  
  
  data.buffer.push("\n                <span class=\"member\">\n                    <span class=\"member member-guest\"><strong class=\"member-name\">Someone</strong></span>\n                </span>\n                ");
  }

function program5(depth0,data) {
  
  var buffer = '', stack1, stack2, hashContexts, hashTypes, options;
  data.buffer.push("\n            <div class=\"wallpost-meta\">\n                <em class=\"timestamp\">");
  hashContexts = {'formatting': depth0};
  hashTypes = {'formatting': "STRING"};
  options = {hash:{
    'formatting': ("X")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "created", options) : helperMissing.call(depth0, "localize", "created", options))));
  data.buffer.push("</em>\n                ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "isAuthor", {hash:{},inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n            </div>\n            ");
  return buffer;
  }
function program6(depth0,data) {
  
  
  data.buffer.push("\n                    <a>Delete</a>\n                ");
  }

  data.buffer.push("<article class=\"wallpost wallpost-system\">\n    \n        <header class=\"wallpost-header\">\n            \n            <span class=\"wallpost-system-type\">\n                <span class=\"flaticon solid wallet-1\"></span> Donation\n            </span>\n            \n            <div class=\"wallpost-member\">\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "author", {hash:{},inverse:self.program(3, program3, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                <span class=\"wallpost-system-action\">Made a donation</span>\n            </div>\n            \n            \n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "created", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            \n        </header>\n\n        <div class=\"wallpost-reactions\">\n            ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.render || depth0.render),stack1 ? stack1.call(depth0, "wallpostReactionList", "reactions", options) : helperMissing.call(depth0, "render", "wallpostReactionList", "reactions", options))));
  data.buffer.push("\n        </div>\n\n    </article>");
  return buffer;
  
});Ember.TEMPLATES['task'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, self=this, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression;

function program1(depth0,data) {
  
  var buffer = '', stack1, stack2, hashContexts, hashTypes, options;
  data.buffer.push("\n            <div class=\"owner-actions\">\n            	<header>\n            		<h3>You're the project owner</h3>\n            		<p>You can edit your tasks</p>\n            	</header>\n\n                \n\n                ");
  hashContexts = {'class': depth0};
  hashTypes = {'class': "STRING"};
  options = {hash:{
    'class': ("btn btn-primary btn-iconed task-delete")
  },inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "projectTaskEdit", "controller.model", options) : helperMissing.call(depth0, "linkTo", "projectTaskEdit", "controller.model", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n            	\n            </div>\n         ");
  return buffer;
  }
function program2(depth0,data) {
  
  
  data.buffer.push("\n                    <span class=\"flaticon solid pencil-3\"></span> Edit Task\n                ");
  }

function program4(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n			 \n			");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isAuthor", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n		");
  return buffer;
  }
function program5(depth0,data) {
  
  var buffer = '', stack1, stack2, hashContexts, hashTypes, options;
  data.buffer.push("  \n		    	<div class=\"owner-actions\">\n                	<header>\n                		<h3>You're the project owner</h3>\n                		<p>You can edit your tasks</p>\n                	</header>\n    \n                    \n    \n                    ");
  hashContexts = {'class': depth0};
  hashTypes = {'class': "STRING"};
  options = {hash:{
    'class': ("btn btn-primary btn-iconed task-edit")
  },inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "projectTaskEdit", "controller.model", options) : helperMissing.call(depth0, "linkTo", "projectTaskEdit", "controller.model", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                	\n                </div>\n		    	 \n			");
  return buffer;
  }
function program6(depth0,data) {
  
  
  data.buffer.push("\n                        <span class=\"flaticon solid pencil-3\"></span> Edit Task\n                    ");
  }

function program8(depth0,data) {
  
  
  data.buffer.push("\n                    <span class=\"flaticon solid clipboard-1\"></span>\n                    Open\n                ");
  }

function program10(depth0,data) {
  
  
  data.buffer.push("\n                    <span class=\"flaticon solid upload-to-clipboard-1\"></span>\n                    In progress\n                ");
  }

function program12(depth0,data) {
  
  
  data.buffer.push("\n                    <span class=\"flaticon solid delete-from-clipboard-1\"></span>\n                    Closed\n                ");
  }

function program14(depth0,data) {
  
  
  data.buffer.push("\n                    <span class=\"flaticon solid clipboard-checkmark-1\"></span>\n                    Realised\n                ");
  }

function program16(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts, options;
  data.buffer.push("\n            	<h2>Task Description</h2>\n            	<p>");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.linebreaks || depth0.linebreaks),stack1 ? stack1.call(depth0, "description", options) : helperMissing.call(depth0, "linebreaks", "description", options))));
  data.buffer.push("</p>\n            	");
  return buffer;
  }

function program18(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts, options;
  data.buffer.push("\n            	<h2>End goal</h2>\n                <p>");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.linebreaks || depth0.linebreaks),stack1 ? stack1.call(depth0, "end_goal", options) : helperMissing.call(depth0, "linebreaks", "end_goal", options))));
  data.buffer.push("</p>\n                ");
  return buffer;
  }

function program20(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes, options;
  data.buffer.push("\n	                    <dd>");
  hashContexts = {'formatting': depth0};
  hashTypes = {'formatting': "STRING"};
  options = {hash:{
    'formatting': ("X")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "deadline", options) : helperMissing.call(depth0, "localize", "deadline", options))));
  data.buffer.push("</dd>\n	                ");
  return buffer;
  }

function program22(depth0,data) {
  
  
  data.buffer.push("\n	                    <dd>No deadline</dd>\n	                ");
  }

function program24(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n	                        ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "tag.id", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                    ");
  return buffer;
  }

function program26(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	            <ul class=\"task-members\">\n	                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "members", {hash:{},inverse:self.noop,fn:self.program(27, program27, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n				</ul>\n				");
  return buffer;
  }
function program27(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n	                    <li class=\"task-member\">\n	                       \n                        	<a>\n                            	<figure class=\"member-avatar\"><img></figure>\n								<strong class=\"member-name\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "member.full_name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong><br>\n								<em class=\"member-status\">\n    								");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isStatusApplied", {hash:{},inverse:self.noop,fn:self.program(28, program28, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isStatusAccepted", {hash:{},inverse:self.noop,fn:self.program(30, program30, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isStatusRejected", {hash:{},inverse:self.noop,fn:self.program(32, program32, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isStatusRealized", {hash:{},inverse:self.noop,fn:self.program(34, program34, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n								</em>\n								<em class=\"timestamp\">");
  hashContexts = {'formatting': depth0};
  hashTypes = {'formatting': "STRING"};
  options = {hash:{
    'formatting': ("X")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "created", options) : helperMissing.call(depth0, "localize", "created", options))));
  data.buffer.push("</em>\n                        	</a>\n							\n							\n	                        ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "controller.isProjectOwner", {hash:{},inverse:self.program(38, program38, data),fn:self.program(36, program36, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n								\n	                    </li>\n	                ");
  return buffer;
  }
function program28(depth0,data) {
  
  
  data.buffer.push("\n                                        Applied\n                                    ");
  }

function program30(depth0,data) {
  
  
  data.buffer.push("\n                                        Started\n                                    ");
  }

function program32(depth0,data) {
  
  
  data.buffer.push("\n                                        Rejected\n                                    ");
  }

function program34(depth0,data) {
  
  
  data.buffer.push("\n                                        Realised\n                                    ");
  }

function program36(depth0,data) {
  
  
  data.buffer.push("\n								<a>\n                            		<span class=\"flaticon solid pencil-3\"></span>\n									Edit Status\n								</a>\n							");
  }

function program38(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n							 \n								");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "controller.isAuthor", {hash:{},inverse:self.noop,fn:self.program(39, program39, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n							");
  return buffer;
  }
function program39(depth0,data) {
  
  
  data.buffer.push("  \n									<a>\n										<span class=\"flaticon solid pencil-3\"></span>\n										Edit Status\n									</a>\n								");
  }

function program41(depth0,data) {
  
  
  data.buffer.push("\n					<p>No member assigned to this task yet.</p>\n				");
  }

function program43(depth0,data) {
  
  
  data.buffer.push("\n	            \n		        ");
  }

function program45(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n		            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "controllers.currentUser.isAuthenticated", {hash:{},inverse:self.program(51, program51, data),fn:self.program(46, program46, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n		        ");
  return buffer;
  }
function program46(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n		                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isStatusRealized", {hash:{},inverse:self.program(49, program49, data),fn:self.program(47, program47, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n		            ");
  return buffer;
  }
function program47(depth0,data) {
  
  
  data.buffer.push("\n		                ");
  }

function program49(depth0,data) {
  
  
  data.buffer.push("\n		                    <a>\n		                        <span class=\"flaticon solid add-to-clipboard-1\"></span> Apply for task\n		                    </a>\n		                ");
  }

function program51(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n		            	<p class=\"login-box\"><a>Login</a> or become a ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(52, program52, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "signup", options) : helperMissing.call(depth0, "linkTo", "signup", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push(" to apply for this task.</p>\n		            ");
  return buffer;
  }
function program52(depth0,data) {
  
  
  data.buffer.push("member");
  }

function program54(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	            <ul class=\"task-files\">\n	                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "files", {hash:{},inverse:self.noop,fn:self.program(55, program55, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	            </ul>\n	            ");
  return buffer;
  }
function program55(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n	                    <li class=\"task-file\">\n	                        <a>\n	                        	<em class=\"flaticon solid download-document-1\"></em>\n								<strong class=\"file-name\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong>\n								<small class=\"file-size\">(");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "file.size", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(")</small>\n	                            <em class=\"file-author\">by ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "author.full_name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</em>\n	                        </a>\n	                    </li>\n	                ");
  return buffer;
  }

function program57(depth0,data) {
  
  
  data.buffer.push("\n					<p>No files have been uploaded yet.</p>\n				");
  }

function program59(depth0,data) {
  
  
  data.buffer.push("\n					<a>\n		                <span class=\"flaticon solid upload-document-1\"></span>\n		                Upload a file\n		            </a>\n				");
  }

function program61(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n				 \n					");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "controller.isAuthor", {hash:{},inverse:self.noop,fn:self.program(62, program62, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n					\n				");
  return buffer;
  }
function program62(depth0,data) {
  
  
  data.buffer.push("  \n						<a>\n			                <span class=\"flaticon solid upload-document-1\"></span>\n			                Upload a file\n			            </a>\n					");
  }

  data.buffer.push("<section class=\"l-wrapper\" id=\"task-detail\">\n    \n        \n		");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isProjectOwner", {hash:{},inverse:self.program(4, program4, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    \n        <div class=\"l-content\">\n            \n            <div class=\"task-status\">\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isStatusOpen", {hash:{},inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isStatusInProgress", {hash:{},inverse:self.noop,fn:self.program(10, program10, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isStatusClosed", {hash:{},inverse:self.noop,fn:self.program(12, program12, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isStatusRealized", {hash:{},inverse:self.noop,fn:self.program(14, program14, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </div>\n            \n            <article class=\"task-description\">\n        \n            	<header class=\"task-header\">\n                    <h1 class=\"task-title\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</h1>\n            	</header>\n                \n                <a>\n                    <strong class=\"member-name\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "author.full_name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong>\n                </a>\n                \n                <em class=\"task-timestamp\">");
  hashContexts = {'formatting': depth0};
  hashTypes = {'formatting': "STRING"};
  options = {hash:{
    'formatting': ("X")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "created", options) : helperMissing.call(depth0, "localize", "created", options))));
  data.buffer.push("</em>\n\n                ");
  hashContexts = {'classNames': depth0};
  hashTypes = {'classNames': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.SocialShareView", {hash:{
    'classNames': ("task-share")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n\n            	");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "description", {hash:{},inverse:self.noop,fn:self.program(16, program16, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n            	\n            	");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "end_goal", {hash:{},inverse:self.noop,fn:self.program(18, program18, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n            </article>\n            \n			<div id=\"wallposts\">\n        		");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.render || depth0.render),stack1 ? stack1.call(depth0, "taskWallpostList", options) : helperMissing.call(depth0, "render", "taskWallpostList", options))));
  data.buffer.push("\n			</div>			\n			\n        </div>\n               	\n		\n		<sidebar class=\"l-sidebar\">\n		\n	        <div class=\"task-section task-meta\">\n	            <h3>Task details</h3>\n	            <dl>\n	                <dt>\n	                    <span class=\"flaticon solid wrench-1\"></span>\n	                    Skill\n	                </dt>\n	                <dd>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "skill.name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</dd>\n	            </dl>\n	            <dl>\n	                <dt>\n	                    <span class=\"flaticon solid location-pin-1\"></span>\n	                    Location\n	                </dt>\n	                <dd>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "location", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</dd>\n	            </dl>\n	            <dl>\n	                <dt>\n	                    <span class=\"flaticon solid watch-1\"></span>\n	                    Time needed\n	                </dt>\n	                <dd>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "timeNeeded", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</dd>\n	            </dl>\n	            <dl>\n	                <dt>\n	                    <span class=\"flaticon solid calendar-1\"></span>\n	                    Deadline\n	                </dt>         \n	                ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "deadline", {hash:{},inverse:self.program(22, program22, data),fn:self.program(20, program20, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n	            </dl>\n	            <dl>          \n	                <dt>\n	                    <span class=\"flaticon solid tag-1\"></span>\n	                    Tags\n	                </dt>\n	                <dd>\n	                    ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers.each.call(depth0, "tag", "in", "tags", {hash:{},inverse:self.noop,fn:self.program(24, program24, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n	                </dd>\n	            </dl>\n	        </div>\n	\n	        <div class=\"task-section\">\n	            <h3>Task members</h3>\n	            ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "members", {hash:{},inverse:self.program(41, program41, data),fn:self.program(26, program26, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n				\n				");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "isMember", {hash:{},inverse:self.program(45, program45, data),fn:self.program(43, program43, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n				\n	        </div>\n	        \n	        <div class=\"task-section\">\n	            <h3>Task files</h3>\n	            \n	            ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "files", {hash:{},inverse:self.program(57, program57, data),fn:self.program(54, program54, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n	            \n	            \n                ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "controller.isProjectOwner", {hash:{},inverse:self.program(61, program61, data),fn:self.program(59, program59, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n	        </div>\n        </sidebar>\n    </section>");
  return buffer;
  
});Ember.TEMPLATES['task_edit'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.title", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                        ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program4(depth0,data) {
  
  var buffer = '', hashContexts, hashTypes;
  data.buffer.push("\n	                                <label for=\"status_open\" class=\"radio\">\n	                                    ");
  hashContexts = {'value': depth0,'id': depth0};
  hashTypes = {'value': "STRING",'id': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': ("open"),
    'id': ("status_open")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                                    <span>Open</span>\n	                                </label>\n	                                <label for=\"status_in_progress\" class=\"radio\">\n	                                    ");
  hashContexts = {'value': depth0,'id': depth0};
  hashTypes = {'value': "STRING",'id': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': ("in progress"),
    'id': ("status_in_progress")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                                    <span>In progress</span>\n	                                </label>\n	                                <label for=\"status_closed\" class=\"radio\">\n	                                    ");
  hashContexts = {'value': depth0,'id': depth0};
  hashTypes = {'value': "STRING",'id': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': ("closed"),
    'id': ("status_closed")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                                    <span>Closed</span>\n	                                </label>\n	                                <label for=\"status_realised\" class=\"radio\">\n	                                    ");
  hashContexts = {'value': depth0,'id': depth0};
  hashTypes = {'value': "STRING",'id': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': ("realized"),
    'id': ("status_realised")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                                    <span>Realised</span>\n	                                </label>\n	                            ");
  return buffer;
  }

function program6(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.status", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                        ");
  return buffer;
  }

function program8(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.description", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                        ");
  return buffer;
  }

function program10(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.end_goal", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                        ");
  return buffer;
  }

function program12(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.dealine", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                        ");
  return buffer;
  }

function program14(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.location", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                        ");
  return buffer;
  }

function program16(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "time_needed.location", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                        ");
  return buffer;
  }

function program18(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.skill", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                        ");
  return buffer;
  }

function program20(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.tags", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                        ");
  return buffer;
  }

  data.buffer.push("<div class=\"l-section\">\n        <section class=\"l-wrapper\">\n        	<form class=\"l-content\" id=\"task-form\">\n        	    <legend>\n    		        <strong>Edit current task</strong>\n    		    </legend>\n    		    \n	            <fieldset>\n	                <ul>\n	                    <li class=\"control-group\">\n	                        <label class=\"control-label\" for=\"task-title\">\n	                            Title of your task.\n	                        </label>\n	\n	                        <div class=\"controls\">\n	                            ");
  hashContexts = {'valueBinding': depth0,'id': depth0,'name': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'id': "STRING",'name': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Ember.TextField", {hash:{
    'valueBinding': ("title"),
    'id': ("task-title"),
    'name': ("task-title"),
    'classBinding': ("errors.title.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                        </div>\n	\n	                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.title", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    </li>\n	                </ul>\n	            </fieldset>\n	            <fieldset>\n	                <ul>\n	                    <li class=\"control-group\">\n	                        <label class=\"control-label\" for=\"task-status\">\n	                            Status\n	                        </label>\n	\n	                        <div class=\"controls\">\n	                            ");
  hashContexts = {'class': depth0,'name': depth0,'selectedValueBinding': depth0};
  hashTypes = {'class': "STRING",'name': "STRING",'selectedValueBinding': "STRING"};
  stack1 = helpers.view.call(depth0, "Em.RadioButtonGroup", {hash:{
    'class': ("radio-select four"),
    'name': ("status"),
    'selectedValueBinding': ("status")
  },inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                        </div>\n	\n	                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.status", {hash:{},inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    </li>\n	                </ul>\n	            </fieldset>\n	            <fieldset>\n	                <ul>\n	                    <li class=\"control-group\">\n	                        <label class=\"control-label\" for=\"task-description\">\n	                            Description.\n	                        </label>\n	\n	                        <div class=\"controls\">\n	                            ");
  hashContexts = {'valueBinding': depth0,'cols': depth0,'rows': depth0,'name': depth0,'id': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'cols': "STRING",'rows': "STRING",'name': "STRING",'id': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Ember.TextArea", {hash:{
    'valueBinding': ("description"),
    'cols': ("50"),
    'rows': ("4"),
    'name': ("task-description"),
    'id': ("task-description"),
    'classBinding': ("errors.description.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                        </div>\n	\n	                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.description", {hash:{},inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    </li>\n	\n	                    <li class=\"control-group\">\n	                        <label class=\"control-label\" for=\"task-end_goal\">\n	                            End goal\n	                        </label>\n	\n	                        <div class=\"controls\">\n	                            ");
  hashContexts = {'valueBinding': depth0,'cols': depth0,'rows': depth0,'name': depth0,'id': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'cols': "STRING",'rows': "STRING",'name': "STRING",'id': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Ember.TextArea", {hash:{
    'valueBinding': ("end_goal"),
    'cols': ("50"),
    'rows': ("2"),
    'name': ("task-end_goal"),
    'id': ("task-end_goal"),
    'classBinding': ("errors.end_goal.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                        </div>\n	\n	                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.end_goal", {hash:{},inverse:self.noop,fn:self.program(10, program10, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    </li>\n	                </ul>\n	            </fieldset>\n	            <fieldset>\n	                <ul>\n	                    <li class=\"control-group\">\n	                        <label class=\"control-label\" for=\"task-deadline\">\n	                            Deadline\n	                        </label>\n	\n	                        <div class=\"controls\">\n	                            ");
  hashContexts = {'valueBinding': depth0,'id': depth0,'name': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'id': "STRING",'name': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.TaskDeadLineDatePicker", {hash:{
    'valueBinding': ("deadline"),
    'id': ("task-deadline"),
    'name': ("task-dealine"),
    'classBinding': ("errors.deadline.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                        </div>\n	\n	                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.dealine", {hash:{},inverse:self.noop,fn:self.program(12, program12, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    </li>\n	\n	                    <li class=\"control-group\">\n	                        <label class=\"control-label\" for=\"task-location\">\n	                            Location\n	                        </label>\n	\n	                        <div class=\"controls\">\n	                            ");
  hashContexts = {'valueBinding': depth0,'id': depth0,'name': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'id': "STRING",'name': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Ember.TextField", {hash:{
    'valueBinding': ("location"),
    'id': ("task-location"),
    'name': ("task-location"),
    'classBinding': ("errors.location.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                        </div>\n	\n	                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.location", {hash:{},inverse:self.noop,fn:self.program(14, program14, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    </li>\n	                </ul>\n	            </fieldset>\n	            <fieldset>\n	                <ul>\n	                    <li class=\"control-group\">\n	                        <label class=\"control-label\" for=\"task-time-needed\">\n	                            Time needed (approximately)\n	                        </label>\n	\n	                        <div class=\"controls\">\n	                            ");
  hashContexts = {'valueBinding': depth0,'id': depth0,'name': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'id': "STRING",'name': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.TimeNeededSelectView", {hash:{
    'valueBinding': ("time_needed"),
    'id': ("task-time-needed"),
    'name': ("task-time-needed"),
    'classBinding': ("errors.time_needed.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                        </div>\n	\n	                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.time_needed", {hash:{},inverse:self.noop,fn:self.program(16, program16, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    </li>\n	\n	                    <li class=\"control-group\">\n	                        <label class=\"control-label\" for=\"task-skill\">\n	                            Skill\n	                        </label>\n	\n	                        <div class=\"controls\">\n	                            ");
  hashContexts = {'valueBinding': depth0,'id': depth0,'name': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'id': "STRING",'name': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.SkillSelectView", {hash:{
    'valueBinding': ("skill"),
    'id': ("task-skill"),
    'name': ("task-skill"),
    'classBinding': ("errors.skill.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                        </div>\n	\n	                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.skill", {hash:{},inverse:self.noop,fn:self.program(18, program18, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    </li>\n	                </ul>\n	            </fieldset>\n	            <fieldset>\n	                <ul>\n	                    <li class=\"control-group\">\n	                        <label class=\"control-label\">Tags</label>\n	                        <div class=\"controls\">\n	                            ");
  hashContexts = {'tagsBinding': depth0,'classBinding': depth0};
  hashTypes = {'tagsBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.TagWidget", {hash:{
    'tagsBinding': ("tags"),
    'classBinding': ("errors.tags.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                        </div>\n	\n	                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.tags", {hash:{},inverse:self.noop,fn:self.program(20, program20, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    </li>\n	\n	                </ul>\n	            </fieldset>\n                <button class=\"btn btn-primary btn-iconed btn-submit\" type=\"submit\"><span class=\"flaticon solid wrench-1\"></span>Save Task</button>\n                <button class=\"btn btn-cancel\"><em class=\"flaticon stroke x-2\"></em> Cancel Changes</button>\n        	</form>\n        </section>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['task_file_new'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.title", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program4(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n		            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.file", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n		        ");
  return buffer;
  }

  data.buffer.push("<fieldset>\n        <ul>\n            <li class=\"control-group\">\n                <label class=\"control-label\" for=\"tile-title\">\n                    Title\n                </label>\n\n                <div class=\"controls\">\n                    ");
  hashContexts = {'valueBinding': depth0,'id': depth0,'name': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'id': "STRING",'name': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Ember.TextField", {hash:{
    'valueBinding': ("title"),
    'id': ("file-title"),
    'name': ("file-title"),
    'classBinding': ("errors.title.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.title", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n            \n            <li class=\"control-group\">\n                <label class=\"control-label\" for=\"tile-file\">\n                    File\n                </label>\n\n                <div class=\"controls\">\n                    <a class=\"btn-link btn-upload\">\n                        ");
  hashContexts = {'fileBinding': depth0,'name': depth0,'id': depth0};
  hashTypes = {'fileBinding': "STRING",'name': "STRING",'id': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.UploadFile", {hash:{
    'fileBinding': ("file"),
    'name': ("file"),
    'id': ("file")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        <span class=\"flaticon solid upload-document-1\"></span>\n                        Upload file\n                    </a>\n                </div>\n                 \n		        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.file", {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </li>\n        </ul>\n    </fieldset>");
  return buffer;
  
});Ember.TEMPLATES['task_list'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                <ul id=\"search-results\">\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "task", "in", "model", {hash:{},inverse:self.program(4, program4, data),fn:self.program(2, program2, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </ul>\n            ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts, options;
  data.buffer.push("\n                        ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.render || depth0.render),stack1 ? stack1.call(depth0, "taskPreview", "task", options) : helperMissing.call(depth0, "render", "taskPreview", "task", options))));
  data.buffer.push("\n                    ");
  return buffer;
  }

function program4(depth0,data) {
  
  
  data.buffer.push("\n                        <li class=\"no-results\">No tasks found.</li>\n                    ");
  }

function program6(depth0,data) {
  
  
  data.buffer.push("\n                <span class=\"is-loading-big\"><img src=\"images/loading.gif\"><em>Loading projects</em></span>\n            ");
  }

  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.render || depth0.render),stack1 ? stack1.call(depth0, "taskSearchForm", options) : helperMissing.call(depth0, "render", "taskSearchForm", options))));
  data.buffer.push("\n    \n    <div class=\"l-section\">\n        <section class=\"l-wrapper\">\n            ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "model.isLoaded", {hash:{},inverse:self.program(6, program6, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n        </section>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['task_member_apply'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', hashContexts, hashTypes, escapeExpression=this.escapeExpression;


  data.buffer.push("<legend>\n        <p>Are you sure you want to apply to this task?</p>\n    </legend>\n    <fieldset>\n        <ul>\n            <li class=\"control-group\">\n                <label class=\"control-label wide\" for=\"motivation\">Motivation</label>\n\n                <div class=\"controls wide\">\n                    ");
  hashContexts = {'valueBinding': depth0,'name': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'name': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Ember.TextArea", {hash:{
    'valueBinding': ("view.motivation"),
    'name': ("motivation"),
    'classBinding': ("errors.motivation.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n            </li>\n        </ul>\n    </fieldset>");
  return buffer;
  
});Ember.TEMPLATES['task_member_edit'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n    <p>\n        <strong>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "member.first_name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" said:</strong><br>\n        <blockquote>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "motivation", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</blockquote>\n    </p>\n    ");
  return buffer;
  }

function program3(depth0,data) {
  
  var buffer = '', hashContexts, hashTypes;
  data.buffer.push("\n        <label for=\"status_applied\" class=\"radio\">\n            ");
  hashContexts = {'value': depth0,'id': depth0};
  hashTypes = {'value': "STRING",'id': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': ("applied"),
    'id': ("status_applied")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n            <span>Applied</span>\n        </label>\n        <label for=\"status_accepted\" class=\"radio\">\n            ");
  hashContexts = {'value': depth0,'id': depth0};
  hashTypes = {'value': "STRING",'id': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': ("accepted"),
    'id': ("status_accepted")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n            <span>Start</span>\n        </label>\n        <label for=\"status_rejected\" class=\"radio\">\n            ");
  hashContexts = {'value': depth0,'id': depth0};
  hashTypes = {'value': "STRING",'id': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': ("rejected"),
    'id': ("status_rejected")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n            <span>Reject</span>\n        </label>\n        <label for=\"status_realised\" class=\"radio\">\n            ");
  hashContexts = {'value': depth0,'id': depth0};
  hashTypes = {'value': "STRING",'id': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': ("realized"),
    'id': ("status_realised")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n            <span>Realised</span>\n        </label>\n    ");
  return buffer;
  }

  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "motivation", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    \n    ");
  hashContexts = {'class': depth0,'name': depth0,'selectedValueBinding': depth0};
  hashTypes = {'class': "STRING",'name': "STRING",'selectedValueBinding': "STRING"};
  stack1 = helpers.view.call(depth0, "Em.RadioButtonGroup", {hash:{
    'class': ("radio-select four"),
    'name': ("status"),
    'selectedValueBinding': ("status")
  },inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  return buffer;
  
});Ember.TEMPLATES['task_new'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.title", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                        ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program4(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.description", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                        ");
  return buffer;
  }

function program6(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.end_goal", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                        ");
  return buffer;
  }

function program8(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.dealine", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                        ");
  return buffer;
  }

function program10(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.location", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                        ");
  return buffer;
  }

function program12(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "time_needed.location", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                        ");
  return buffer;
  }

function program14(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.skill", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                        ");
  return buffer;
  }

function program16(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.tags", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	                        ");
  return buffer;
  }

  data.buffer.push("<div class=\"l-section\">\n        <section class=\"l-wrapper\">\n    		<form class=\"l-content\" id=\"task-form\">\n    		    <legend>\n    		        <strong>Create new task</strong>\n    		    </legend>\n	            <fieldset>\n	                <ul>\n	                    <li class=\"control-group\">\n	                        <label class=\"control-label\" for=\"task-title\">\n	                            Title of your task\n	                        </label>\n	\n	                        <div class=\"controls\">\n	                            ");
  hashContexts = {'valueBinding': depth0,'id': depth0,'name': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'id': "STRING",'name': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Ember.TextField", {hash:{
    'valueBinding': ("title"),
    'id': ("task-title"),
    'name': ("task-title"),
    'classBinding': ("errors.title.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                        </div>\n	\n	                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.title", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    </li>\n	                    \n	                    <li class=\"control-group\">\n	                        <label class=\"control-label\" for=\"task-description\">\n	                            Description\n	                        </label>\n	\n	                        <div class=\"controls\">\n	                            ");
  hashContexts = {'valueBinding': depth0,'cols': depth0,'rows': depth0,'name': depth0,'id': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'cols': "STRING",'rows': "STRING",'name': "STRING",'id': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Ember.TextArea", {hash:{
    'valueBinding': ("description"),
    'cols': ("50"),
    'rows': ("4"),
    'name': ("task-description"),
    'id': ("task-description"),
    'classBinding': ("errors.description.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                        </div>\n	\n	                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.description", {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    </li>\n	\n	                    <li class=\"control-group\">\n	                        <label class=\"control-label\" for=\"task-end_goal\">\n	                            End goal\n	                        </label>\n	\n	                        <div class=\"controls\">\n	                            ");
  hashContexts = {'valueBinding': depth0,'cols': depth0,'rows': depth0,'name': depth0,'id': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'cols': "STRING",'rows': "STRING",'name': "STRING",'id': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Ember.TextArea", {hash:{
    'valueBinding': ("end_goal"),
    'cols': ("50"),
    'rows': ("2"),
    'name': ("task-end_goal"),
    'id': ("task-end_goal"),
    'classBinding': ("errors.end_goal.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                        </div>\n	\n	                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.end_goal", {hash:{},inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    </li>\n	                </ul>\n	            </fieldset>\n	            <fieldset>\n	                <ul>\n	                    <li class=\"control-group\">\n	                        <label class=\"control-label\" for=\"task-deadline\">\n	                            Dead line\n	                        </label>\n	\n	                        <div class=\"controls\">\n	                            ");
  hashContexts = {'valueBinding': depth0,'id': depth0,'name': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'id': "STRING",'name': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.TaskDeadLineDatePicker", {hash:{
    'valueBinding': ("deadline"),
    'id': ("task-deadline"),
    'name': ("task-dealine"),
    'classBinding': ("errors.deadline.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                        </div>\n	\n	                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.dealine", {hash:{},inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    </li>\n	\n	                    <li class=\"control-group\">\n	                        <label class=\"control-label\" for=\"task-location\">\n	                            Location\n	                        </label>\n	\n	                        <div class=\"controls\">\n	                            ");
  hashContexts = {'valueBinding': depth0,'id': depth0,'name': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'id': "STRING",'name': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Ember.TextField", {hash:{
    'valueBinding': ("location"),
    'id': ("task-location"),
    'name': ("task-location"),
    'classBinding': ("errors.location.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                        </div>\n	\n	                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.location", {hash:{},inverse:self.noop,fn:self.program(10, program10, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    </li>\n	                </ul>\n	            </fieldset>\n	            <fieldset>\n	                <ul>\n	                    <li class=\"control-group\">\n	                        <label class=\"control-label\" for=\"task-time-needed\">\n	                            Time needed (approximately)\n	                        </label>\n	\n	                        <div class=\"controls\">\n	                            ");
  hashContexts = {'valueBinding': depth0,'id': depth0,'name': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'id': "STRING",'name': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.TimeNeededSelectView", {hash:{
    'valueBinding': ("time_needed"),
    'id': ("task-time-needed"),
    'name': ("task-time-needed"),
    'classBinding': ("errors.time_needed.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                        </div>\n	\n	                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.time_needed", {hash:{},inverse:self.noop,fn:self.program(12, program12, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    </li>\n	\n	                    <li class=\"control-group\">\n	                        <label class=\"control-label\" for=\"task-skill\">\n	                            Skill\n	                        </label>\n	\n	                        <div class=\"controls\">\n	                            ");
  hashContexts = {'valueBinding': depth0,'id': depth0,'name': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'id': "STRING",'name': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.SkillSelectView", {hash:{
    'valueBinding': ("skill"),
    'id': ("task-skill"),
    'name': ("task-skill"),
    'classBinding': ("errors.skill.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                        </div>\n	\n	                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.skill", {hash:{},inverse:self.noop,fn:self.program(14, program14, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    </li>\n	                </ul>\n	            </fieldset>\n	            <fieldset>\n	                <ul>\n	                    <li class=\"control-group\">\n	                        <label class=\"control-label\">Tags</label>\n	                        <div class=\"controls\">\n	                            ");
  hashContexts = {'tagsBinding': depth0,'classBinding': depth0};
  hashTypes = {'tagsBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.TagWidget", {hash:{
    'tagsBinding': ("tags"),
    'classBinding': ("errors.tags.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                        </div>\n	\n	                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.tags", {hash:{},inverse:self.noop,fn:self.program(16, program16, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    </li>\n	                </ul>\n	            </fieldset>\n				<button class=\"btn btn-primary btn-iconed btn-submit\" type=\"submit\"><span class=\"flaticon solid wrench-1\"></span>Create Task</button>\n        	</form>\n        </section>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['task_preview'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  
  data.buffer.push("\n	                        <span class=\"flaticon solid clipboard-1\"></span>\n	                        Open\n	                    ");
  }

function program3(depth0,data) {
  
  
  data.buffer.push("\n	                        <span class=\"flaticon solid upload-to-clipboard-1\"></span>\n	                        In progress\n	                    ");
  }

function program5(depth0,data) {
  
  
  data.buffer.push("\n	                        <span class=\"flaticon solid delete-from-clipboard-1\"></span>\n	                        Closed\n	                    ");
  }

function program7(depth0,data) {
  
  
  data.buffer.push("\n	                        <span class=\"flaticon solid clipboard-checkmark-1\"></span>\n	                        Realised\n	                    ");
  }

function program9(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes, options;
  data.buffer.push("\n	                <li>\n	                	<span class=\"flaticon solid calendar-1\"></span>\n	                    ");
  hashContexts = {'formatting': depth0};
  hashTypes = {'formatting': "STRING"};
  options = {hash:{
    'formatting': ("X")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "task.deadline", options) : helperMissing.call(depth0, "localize", "task.deadline", options))));
  data.buffer.push("\n	                </li>\n	                ");
  return buffer;
  }

  data.buffer.push("<li class=\"task-item\">\n    	<a ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.action.call(depth0, "showTask", "task", {hash:{},contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(">\n    	\n    	    <h2 class=\"task-category\"><span class=\"flaticon solid wrench-1\"></span> ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "task.skill.name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</h2>\n    	\n    	    <span class=\"task-header\">\n                <span class=\"task-image\">\n                	<img>\n            	</span>\n                <span class=\"task-title\">\n                	<h3>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "task.title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</h3>\n                	<h4>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</h4> \n                </span>\n            </span>\n            \n	        <div class=\"task-status\">\n	            <ul class=\"task-meta\">\n	                <li>\n	                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "task.isStatusOpen", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "task.isStatusInProgress", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "task.isStatusClosed", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "task.isStatusRealized", {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	\n	                </li>\n	                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.unless.call(depth0, "task.isStatusRealized", {hash:{},inverse:self.noop,fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	                <li>\n	                    <span class=\"flaticon solid watch-1\"></span>\n	                    ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "task.timeNeeded", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                </li>\n	                <li>\n	                	<span class=\"flaticon solid location-pin-1\"></span>\n	                	");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.country.name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	                </li>\n	            </ul>\n	        </div>\n	        \n	        <div class=\"task-description\">\n	            ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "task.description", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n    	        \n    	        <span class=\"task-view\">View task</span>\n	        </div>\n	        \n    	</a>\n    </li>");
  return buffer;
  
});Ember.TEMPLATES['task_search_form'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("Showing ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "rangeStart", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("-");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "rangeEnd", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  return buffer;
  }

function program3(depth0,data) {
  
  
  data.buffer.push("\n		                    <a>\n		                        <span class=\"flaticon solid left-circle-2\"></span>\n		                    </a>\n		                ");
  }

function program5(depth0,data) {
  
  
  data.buffer.push("\n		                	<span class=\"previous-page\"><span class=\"flaticon solid left-circle-2\"></span></span>\n		                ");
  }

function program7(depth0,data) {
  
  
  data.buffer.push("\n		                    <a>\n		                        <span class=\"flaticon solid right-circle-2\"></span>\n		                    </a>\n		                ");
  }

function program9(depth0,data) {
  
  
  data.buffer.push("\n		                	<span class=\"next-page\"><span class=\"flaticon solid right-circle-2\"></span></span>\n		                ");
  }

  data.buffer.push("<div class=\"l-section\" id=\"search\">\n        <section class=\"l-wrapper\">\n            <form id=\"search-form\">\n                <div class=\"control\">\n                    <span class=\"flaticon stroke wrench-1\"></span>\n                    ");
  hashContexts = {'valueBinding': depth0};
  hashTypes = {'valueBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.SkillSelectView", {hash:{
    'valueBinding': ("skill")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n                <div class=\"control\">\n                    <span class=\"flaticon stroke inbox-1\"></span>\n                    ");
  hashContexts = {'valueBinding': depth0};
  hashTypes = {'valueBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.TaskStatusSelectView", {hash:{
    'valueBinding': ("status")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </div>\n            </form>\n        </section>\n    </div>\n    \n    <div class=\"l-section\">\n        <section class=\"l-wrapper\">\n            <article id=\"search-navigation\">\n            	\n            	<header>\n                	<h2>Results <em>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "controllers.taskList.model.meta.total", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</em></h2>\n                	<a>\n                        <span class=\"flaticon solid x-2\"></span> Reset\n                    </a>\n            	</header>\n            	\n                <div class=\"search-sort\">\n                    <strong>Sort:</strong>\n                    <a>Newest</a>\n                    <a>Near deadline</a>\n                </div>\n                \n                <div class=\"search-pagination\">\n                	<span class=\"search-showing\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "controllers.taskList.model.meta.total", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</span>\n                	<span class=\"search-pages-control\">\n		                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "hasPreviousPage", {hash:{},inverse:self.program(5, program5, data),fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n		                \n		                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "hasNextPage", {hash:{},inverse:self.program(9, program9, data),fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                	</span>\n                </div>\n                \n            </article>\n        </section>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['task_wallpost'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, options, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes, options;
  data.buffer.push("\n                    <em class=\"timestamp\">");
  hashContexts = {'formatting': depth0};
  hashTypes = {'formatting': "STRING"};
  options = {hash:{
    'formatting': ("X")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "created", options) : helperMissing.call(depth0, "localize", "created", options))));
  data.buffer.push("</em>\n                ");
  return buffer;
  }

function program3(depth0,data) {
  
  
  data.buffer.push("\n                    <a>Delete</a>\n                ");
  }

  data.buffer.push("<article class=\"wallpost\">\n    \n        <header class=\"wallpost-header\">\n        \n            <div class=\"wallpost-member\">\n                <a ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.action.call(depth0, "openInBigBox", "memberProfile", "author", {hash:{},contexts:[depth0,depth0,depth0],types:["ID","STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" class=\"member\">\n                    <span class=\"member-avatar\">\n                        <img ");
  hashContexts = {'src': depth0};
  hashTypes = {'src': "STRING"};
  data.buffer.push(escapeExpression(helpers.bindAttr.call(depth0, {hash:{
    'src': ("author.getAvatar")
  },contexts:[],types:[],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" alt=\"");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "author.full_name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\"  />\n                    </span>\n                    <strong class=\"member-name\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "author.full_name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong>\n                </a>\n            </div>\n            \n            <div class=\"wallpost-meta\">\n                 ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "created", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isAuthor", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </div>\n        </header>\n\n        <div class=\"wallpost-content\">\n            <div class=\"text\">");
  hashContexts = {'unescaped': depth0};
  hashTypes = {'unescaped': "STRING"};
  stack1 = helpers._triageMustache.call(depth0, "text", {hash:{
    'unescaped': ("true")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	    </div>\n        \n        <div class=\"wallpost-reactions\">\n            ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.render || depth0.render),stack1 ? stack1.call(depth0, "wallpostReactionList", "reactions", options) : helperMissing.call(depth0, "render", "wallpostReactionList", "reactions", options))));
  data.buffer.push("\n        </div>\n\n    </article>");
  return buffer;
  
});Ember.TEMPLATES['task_wallpost_list'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts, options;
  data.buffer.push("\n	        ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.render || depth0.render),stack1 ? stack1.call(depth0, "taskWallpostNew", options) : helperMissing.call(depth0, "render", "taskWallpostNew", options))));
  data.buffer.push("\n	    ");
  return buffer;
  }

function program3(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n	        <div class=\"login-box\"><a ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.action.call(depth0, "openInBox", "login", {hash:{},contexts:[depth0,depth0],types:["ID","STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(">Login</a> or become a ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "signup", options) : helperMissing.call(depth0, "linkTo", "signup", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push(" to leave a reaction.</div>\n	    ");
  return buffer;
  }
function program4(depth0,data) {
  
  
  data.buffer.push("member");
  }

function program6(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "item.isLoaded", {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    ");
  return buffer;
  }
function program7(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n            ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.TaskWallpostView", {hash:{},contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n        ");
  return buffer;
  }

function program9(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n        <a>\n            <span class=\"flaticon solid plus-2\"></span> Show more <small>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "remainingItemCount", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" more</small>\n        </a>\n    ");
  return buffer;
  }

  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "controllers.currentUser.isAuthenticated", {hash:{},inverse:self.program(3, program3, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n    ");
  hashContexts = {'itemController': depth0};
  hashTypes = {'itemController': "STRING"};
  stack1 = helpers.each.call(depth0, "item", "in", "items", {hash:{
    'itemController': ("wallpost")
  },inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "canLoadMore", {hash:{},inverse:self.noop,fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  return buffer;
  
});Ember.TEMPLATES['task_wallpost_new'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                	<div class=\"errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.text", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n					");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

  data.buffer.push("<form id=\"wallpost-form\">\n	    <fieldset>\n		   <ul>\n		        <li class=\"control-group\">\n		            <label for=\"wallpost-update\" class=\"control-label\">Comment</label>\n		\n		            <div class=\"controls\">\n		                ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'cols': depth0,'rows': depth0,'name': depth0,'id': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'cols': "STRING",'rows': "STRING",'name': "STRING",'id': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Ember.TextArea", {hash:{
    'valueBinding': ("text"),
    'placeholder': ("Comment"),
    'cols': ("50"),
    'rows': ("2"),
    'name': ("wallpost-update"),
    'id': ("wallpost-update")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n		            </div>\n		\n		            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.text", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n		        </li>\n		    </ul>\n		</fieldset>\n	\n	    <button><span class=\"flaticon solid thinking-comment-1\"></span>Comment</button>\n    </form>");
  return buffer;
  
});Ember.TEMPLATES['text_wallpost_new'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n	                <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.text", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n	            ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

  data.buffer.push("<fieldset>\n	   <ul>\n	        <li class=\"control-group\">\n	            <label for=\"wallpost-update\" class=\"control-label\">Comment</label>\n	\n	            <div class=\"controls\">\n	                ");
  hashContexts = {'valueBinding': depth0,'cols': depth0,'rows': depth0,'name': depth0,'id': depth0};
  hashTypes = {'valueBinding': "STRING",'cols': "STRING",'rows': "STRING",'name': "STRING",'id': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Ember.TextArea", {hash:{
    'valueBinding': ("text"),
    'cols': ("50"),
    'rows': ("4"),
    'name': ("wallpost-update"),
    'id': ("wallpost-update")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n	            </div>\n	\n	            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.text", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n	        </li>\n	    </ul>\n	</fieldset>\n\n    <button class=\"btn btn-iconed\" type=\"submit\"><span class=\"flaticon solid thinking-comment-1\"></span>Comment</button>");
  return buffer;
  
});Ember.TEMPLATES['ticker'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, helperMissing=helpers.helperMissing, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes, options;
  data.buffer.push("\n            <li class=\"donation-project\">\n                <img ");
  hashContexts = {'src': depth0,'alt': depth0};
  hashTypes = {'src': "STRING",'alt': "STRING"};
  data.buffer.push(escapeExpression(helpers.bindAttr.call(depth0, {hash:{
    'src': ("donation.project.image"),
    'alt': ("project.title")
  },contexts:[],types:[],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" class=\"project-image\" style=\"width: 200px; float: right;\"  />\n                <img ");
  hashContexts = {'src': depth0,'alt': depth0};
  hashTypes = {'src': "STRING",'alt': "STRING"};
  data.buffer.push(escapeExpression(helpers.bindAttr.call(depth0, {hash:{
    'src': ("donation.user.avatar"),
    'alt': ("project.title")
  },contexts:[],types:[],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" class=\"project-image\"  style=\"width: 150px\"   />\n                <strong style=\"font-size:70px; padding: 10px; font-weight: 600; color: #ff619a; float: right;\">&euro;");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "donation.amount", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong><br>\n                <h2 style=\"font-size:30px; color: black;\">\n                    ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "donation.user.full_name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("<br>\n                    <span style=\"color: #777;font-size:20px; text-transform: lowercase\">");
  hashContexts = {'formatting': depth0};
  hashTypes = {'formatting': "STRING"};
  options = {hash:{
    'formatting': ("X")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "donation.created", options) : helperMissing.call(depth0, "localize", "donation.created", options))));
  data.buffer.push("</span><br>\n                    <span style=\"color: #777;\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "donation.project.title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</span>\n                </h2>\n\n            </li>\n        ");
  return buffer;
  }

  data.buffer.push("<ul class=\"donation-projects\" >\n        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "donation", "in", "controller", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    </ul>");
  return buffer;
  
});Ember.TEMPLATES['user'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, escapeExpression=this.escapeExpression, self=this, helperMissing=helpers.helperMissing;

function program1(depth0,data) {
  
  
  data.buffer.push("\n                        <span class=\"tab-icon amount\"><em class=\"flaticon solid user-2\"></em></span>\n                        <strong class=\"tab-title\">Profile <em class=\"tab-subtitle\">Public info</em></strong>\n                    ");
  }

function program3(depth0,data) {
  
  
  data.buffer.push("\n                        <span class=\"tab-icon amount\"><em class=\"flaticon solid settings-2\"></em></span>\n                        <strong class=\"tab-title\">Account <em class=\"tab-subtitle\">Settings</em></strong>\n                    ");
  }

function program5(depth0,data) {
  
  
  data.buffer.push("\n                        <em class=\"tab-icon amount\"><i class=\"flaticon solid wallet-1\"></i></em>\n                        <strong class=\"tab-title\">Payment <em class=\"tab-subtitle\">Orders</em></strong>\n                    ");
  }

  data.buffer.push("<div id=\"profile\">\n    <div class=\"l-section profile-actions\">\n        <nav class=\"l-wrapper\">\n        \n            <div class=\"profile-actions-meta\">\n                <a ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.action.call(depth0, "openInBigBox", "userModal", "controllers.currentUser.content", {hash:{},contexts:[depth0,depth0,depth0],types:["ID","STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(">\n                    <img ");
  hashContexts = {'src': depth0};
  hashTypes = {'src': "STRING"};
  data.buffer.push(escapeExpression(helpers.bindAttr.call(depth0, {hash:{
    'src': ("controllers.currentUser.getAvatar")
  },contexts:[],types:[],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("  />\n                    <span class=\"profile-actions-meta-title\">\n                        My 1%\n                        \n                        <span class=\"profile-title\">\n                            Profile\n                        </span>\n\n                        <small>\n                            <em class=\"flaticon solid eye-1\"></em>\n                            Preview my profile\n                        </small>\n                    </span>\n                </a>\n            </div>\n            \n            <ul class=\"tabs\">\n                <li class=\"tab-item first\">\n                    ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "userProfile", options) : helperMissing.call(depth0, "linkTo", "userProfile", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                </li>\n\n                <li class=\"tab-item\">\n                    ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "userSettings", options) : helperMissing.call(depth0, "linkTo", "userSettings", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                </li>\n\n                <li class=\"tab-item\">\n                    ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "userOrders", options) : helperMissing.call(depth0, "linkTo", "userOrders", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                </li>\n            </ul>\n            \n        </nav>\n    </div>\n\n    \n    ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "outlet", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n\n</div>");
  return buffer;
  
});Ember.TEMPLATES['userDonation'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashContexts, hashTypes, options, escapeExpression=this.escapeExpression, self=this, helperMissing=helpers.helperMissing;

function program1(depth0,data) {
  
  
  data.buffer.push("\n                        <em class=\"tab-icon\"><span class=\"flaticon solid wallet-1\"></span></em>\n                        <strong class=\"tab-title\">\n                            Monthly Donation\n                            <em class=\"tab-subtitle\">Select Projects</em>\n                        </strong>\n                    ");
  }

function program3(depth0,data) {
  
  
  data.buffer.push("\n                        <em class=\"tab-icon\"><span class=\"flaticon solid wallet-1\"></span></em>\n                        <strong class=\"tab-title\">\n                            Donation Profile\n                            <em class=\"tab-subtitle\">Payment Details</em>\n                        </strong>\n                    ");
  }

function program5(depth0,data) {
  
  
  data.buffer.push("\n                        <em class=\"tab-icon\"><span class=\"flaticon solid wallet-1\"></span></em>\n                        <strong class=\"tab-title\">\n                            Donations\n                            <em class=\"tab-subtitle\">Donation History</em>\n                        </strong>\n                    ");
  }

  data.buffer.push("<div id=\"account\">\n\n    <div class=\"l-section account-header\">\n        <nav class=\"l-wrapper\">    \n            <figure class=\"account-avatar\"><img ");
  hashContexts = {'src': depth0};
  hashTypes = {'src': "STRING"};
  data.buffer.push(escapeExpression(helpers.bindAttr.call(depth0, {hash:{
    'src': ("controllers.currentUser.getAvatar")
  },contexts:[],types:[],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("  /></figure>\n            \n            <header class=\"account-title\">\n                <h2>My 1%  <em class=\"account-subtitle\">Donations</em></h2>\n            </header>\n            \n            <ul class=\"tabs three\">\n                <li class=\"tab-item\">\n                    ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "userMonthlyProjects", options) : helperMissing.call(depth0, "linkTo", "userMonthlyProjects", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                </li>\n    \n                <li class=\"tab-item\">\n                    ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "userMonthlyProfile", options) : helperMissing.call(depth0, "linkTo", "userMonthlyProfile", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                </li>\n    \n                <li class=\"tab-item first\">\n                    ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "userDonationHistory", options) : helperMissing.call(depth0, "linkTo", "userDonationHistory", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                </li>\n            </ul>\n        </nav>\n    </div>\n        \n    <div class=\"l-section account-details\">\n        ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "outlet", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n    </div>\n    \n</div>");
  return buffer;
  
});Ember.TEMPLATES['userDonationHistory'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, helperMissing=helpers.helperMissing, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n        \n            <table class=\"fund-history\">\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "order", "in", "controller", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </table>\n        ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', stack1, stack2, hashContexts, hashTypes, options;
  data.buffer.push("\n                <tr>\n                    <td class=\"fund-history-date\">");
  hashContexts = {'formatting': depth0};
  hashTypes = {'formatting': "STRING"};
  options = {hash:{
    'formatting': ("d")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "order.created", options) : helperMissing.call(depth0, "localize", "order.created", options))));
  data.buffer.push("</td>\n                    <td class=\"fund-history-type\">");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "order.recurring", {hash:{},inverse:self.program(5, program5, data),fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("</td>\n                    <td class=\"fund-history-total\">&euro;");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "order.total", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(",-</td>\n                    <td>\n                        <table>\n                            ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers.each.call(depth0, "donation", "in", "order.donations", {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                        </table>\n                    </td>\n                </tr>\n                ");
  return buffer;
  }
function program3(depth0,data) {
  
  
  data.buffer.push(" Monthly Donation ");
  }

function program5(depth0,data) {
  
  
  data.buffer.push(" Single Donation ");
  }

function program7(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                            <tr>\n                                <td class=\"fund-history-project\"><a>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "donation.project.title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</a></td>\n                                <td class=\"fund-history-amount\">&euro;");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "donation.amount", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(",-</td>\n                            </tr>\n                            ");
  return buffer;
  }

function program9(depth0,data) {
  
  
  data.buffer.push("\n            <div class=\"is-loading-small\"><img src=\"images/loading.gif\"> <strong>Loading order history</strong></div>\n        ");
  }

  data.buffer.push("<section class=\"l-wrapper\">\n    <div class=\"l-full\">\n        \n        <header class=\"page-header\">\n            <h1>Order History</h1>\n        </header>\n        \n        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "model.isLoaded", {hash:{},inverse:self.program(9, program9, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            \n    </div>\n</section>");
  return buffer;
  
});Ember.TEMPLATES['userMonthlyProfile'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n                    <legend>\n                        <strong>Edit your payment info</strong>\n                        <p>Here you can change your bank account info and monthly donations.</p>\n                    </legend>\n\n                    <fieldset>\n                        <ul>\n                            <li class=\"control-group\">\n                                <label class=\"control-label\">Account Name</label>\n                                <div class=\"controls\">\n                                    ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("name"),
    'placeholder': ("Full name as it appears on your bank account"),
    'classBinding': ("errors.name.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                                </div>\n                                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.name", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                            </li>\n\n                            <li class=\"control-group\">\n                                <label class=\"control-label\">Account Number</label>\n                                <div class=\"controls\">\n                                    ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("account"),
    'placeholder': ("Your bank account number"),
    'classBinding': ("errors.account.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                                </div>\n                                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.account", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                            </li>\n\n                            <li class=\"control-group\">\n                                <label class=\"control-label\">Account City</label>\n                                <div class=\"controls\">\n                                    ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("city"),
    'placeholder': ("City registered on your bank account"),
    'classBinding': ("errors.city.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                                </div>\n                                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.city", {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                            </li>\n\n                        </ul>\n                    </fieldset>\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "saved", {hash:{},inverse:self.noop,fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n                    <button>\n                        <span class=\"flaticon solid checkmark-1\"></span>\n                        Save\n                    </button>\n                ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.name", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                                ");
  return buffer;
  }
function program3(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program5(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.account", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                                ");
  return buffer;
  }

function program7(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                                    <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.city", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                                ");
  return buffer;
  }

function program9(depth0,data) {
  
  
  data.buffer.push("\n                        <div class=\"is-saved\"><span class=\"flaticon solid checkmark-1\"></span> <strong>Monthly settings saved</strong></div>\n                    ");
  }

  data.buffer.push("<section class=\"l-wrapper\">\n        <div class=\"l-content\">\n            <form>\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "model", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </form>\n        </div>\n    </section>");
  return buffer;
  
});Ember.TEMPLATES['userMonthlyProjects'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, self=this, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression;

function program1(depth0,data) {
  
  
  data.buffer.push("\n                <h1>My monthly donation</h1>\n                <p></p>\n            ");
  }

function program3(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "payment.isNew", {hash:{},inverse:self.program(6, program6, data),fn:self.program(4, program4, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            ");
  return buffer;
  }
function program4(depth0,data) {
  
  
  data.buffer.push("\n                    \n                    <h1>Support 1%Projects monthly</h1>\n                    \n<p>Do you like to support projects regularly on 1%Club? But are you too busy to select a new project each time again?</p>\n<p>No worries! Just set a monthly donation.</p>\n\n<p>\n    There are two ways:\n    <ol>\n        <li>\n            <h3>Top 3 Projects</h3>\n            Follow the 'wisdom of the crowd' and donate to the 3 projects that are most successful that month. And give them an extra boost!\n        </li>\n        <li>\n            <h3>Pick your own project(s)</h3>\n            Select one or more projects yourself that you want to support every month. You can adjust your support all the time, as you like.\n        </li>\n\n    </ol>\n</p>\n<p>We will send you an email every month to update you what project(s) received your 1% support!</p>\n                    \n                    <a><span class=\"flaticon solid checkmark-1\"></span> Yes, I want to set a monthly donation</a>\n                ");
  }

function program6(depth0,data) {
  
  
  data.buffer.push("\n                    \n                    <h1>Monthly donation: <em>Off</em></h1>\n                    <p></p>\n                    <a><span class=\"flaticon solid checkmark-1\"></span> Turn monthly donations on</a>\n                ");
  }

function program8(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <ul class=\"project-list\">\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "donations.length", {hash:{},inverse:self.noop,fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "donation", "in", "donations", {hash:{},inverse:self.program(13, program13, data),fn:self.program(11, program11, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </ul>\n                    \n                    <fieldset class=\"fund-total\">\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "showTopThreeProjects", {hash:{},inverse:self.program(18, program18, data),fn:self.program(16, program16, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                        <div class=\"fund-amount-control\">\n                            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "error", "in", "payment.errors.amount", {hash:{},inverse:self.noop,fn:self.program(20, program20, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                            <label for=\"fund-amount-1\">Divide to projects</label>\n                            <span class=\"currency\"><em>&euro; </em>\n                                ");
  hashContexts = {'type': depth0,'class': depth0,'id': depth0,'step': depth0,'name': depth0,'size': depth0,'maxlength': depth0,'valueBinding': depth0};
  hashTypes = {'type': "STRING",'class': "STRING",'id': "STRING",'step': "STRING",'name': "STRING",'size': "STRING",'maxlength': "STRING",'valueBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'type': ("number"),
    'class': ("fund-amount-input"),
    'id': ("fund-amount-1"),
    'step': ("5"),
    'name': ("fund-amount-1"),
    'size': ("8"),
    'maxlength': ("4"),
    'valueBinding': ("payment.amount")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                            </span>\n                        </div>\n                    </fieldset>\n                    \n                     <a>\n                        <span class=\"flaticon solid plus-2\"></span>\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "donations.length", {hash:{},inverse:self.program(24, program24, data),fn:self.program(22, program22, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </a>\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "payment.isIncomplete", {hash:{},inverse:self.noop,fn:self.program(26, program26, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                ");
  return buffer;
  }
function program9(depth0,data) {
  
  
  data.buffer.push("\n                            <strong>Your monthly donation will go to the project(s) you've selected here:</strong>\n                        ");
  }

function program11(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts, options;
  data.buffer.push("\n                            ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.render || depth0.render),stack1 ? stack1.call(depth0, "monthlyDonation", "donation", options) : helperMissing.call(depth0, "render", "monthlyDonation", "donation", options))));
  data.buffer.push("\n                        ");
  return buffer;
  }

function program13(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <legend class=\"fund-empty\">\n                                <strong>Your monthly donation will got to the top 3 projects.</strong>\n                                <p>The three most popular projects at this moment are:</p>\n                            </legend>    \n                            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "project", "in", "topThreeProjects", {hash:{},inverse:self.noop,fn:self.program(14, program14, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                        ");
  return buffer;
  }
function program14(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                                <li class=\"project-list-item project-top3\">\n                                    \n                                    <a>\n                                        <figure class=\"project-image\">\n                                            <img>\n                                        </figure>\n                                        <h2 class=\"project-title\">\n                                            ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                                            <em class=\"project-location\">\n                                                <span class=\"flaticon solid location-pin-1\"></span> ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.country.name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                                            </em>\n                                        </h2>\n                                    </a>\n                                    \n                                    <div class=\"fund-amount\">\n                                        <strong class=\"fund-amount-needed\">&euro; ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.campaign.money_needed", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong> is still needed\n                                    </div>\n                                </li>\n                            ");
  return buffer;
  }

function program16(depth0,data) {
  
  
  data.buffer.push("\n                            <div class=\"fund-total-label\">&nbsp;</div>\n                        ");
  }

function program18(depth0,data) {
  
  
  data.buffer.push("\n                            <div class=\"fund-total-label\">Total</div>\n                        ");
  }

function program20(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                                <span class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "error", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</span>\n                            ");
  return buffer;
  }

function program22(depth0,data) {
  
  
  data.buffer.push("\n                            Add another project\n                        ");
  }

function program24(depth0,data) {
  
  
  data.buffer.push("\n                            Select a project yourself\n                        ");
  }

function program26(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n                        <h2>My payment details</h2>\n                        <fieldset>\n                            <ul>\n                                <li class=\"control-group\">\n                                    <label class=\"control-label\">Account Name</label>\n                                    <div class=\"controls\">\n                                        ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("payment.name"),
    'placeholder': ("Full name as it appears on your bank account"),
    'classBinding': ("payment.errors.name.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                                    </div>\n                                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "payment.errors.name", {hash:{},inverse:self.noop,fn:self.program(27, program27, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                                </li>\n\n                                <li class=\"control-group\">\n                                    <label class=\"control-label\">Account Number</label>\n                                    <div class=\"controls\">\n                                        ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("payment.account"),
    'placeholder': ("Your bank account number"),
    'classBinding': ("payment.errors.account.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                                    </div>\n                                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "payment.errors.account", {hash:{},inverse:self.noop,fn:self.program(30, program30, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                                </li>\n\n                                <li class=\"control-group\">\n                                    <label class=\"control-label\">Account City</label>\n                                    <div class=\"controls\">\n                                        ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("payment.city"),
    'placeholder': ("City registered on your bank account"),
    'classBinding': ("payment.errors.city.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                                    </div>\n                                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "payment.errors.city", {hash:{},inverse:self.noop,fn:self.program(32, program32, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                                </li>\n\n                            </ul>\n                        </fieldset>\n                        \n                    ");
  return buffer;
  }
function program27(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "payment.errors.name", {hash:{},inverse:self.noop,fn:self.program(28, program28, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                                    ");
  return buffer;
  }
function program28(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program30(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "payment.errors.account", {hash:{},inverse:self.noop,fn:self.program(28, program28, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                                    ");
  return buffer;
  }

function program32(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                                        <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "payment.errors.city", {hash:{},inverse:self.noop,fn:self.program(28, program28, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                                    ");
  return buffer;
  }

function program34(depth0,data) {
  
  
  data.buffer.push("\n                <button>\n                    <span class=\"flaticon solid checkmark-1\"></span>\n                    Save\n                </button>\n                ");
  }

function program36(depth0,data) {
  
  
  data.buffer.push("\n                <a class=\"btn-link\">\n                    <span class=\"flaticon solid x-2\"></span>\n                    Cancel my monthly donation\n                </a>\n            ");
  }

function program38(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts, options;
  data.buffer.push("\n        ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.render || depth0.render),stack1 ? stack1.call(depth0, "monthlyProjectList", options) : helperMissing.call(depth0, "render", "monthlyProjectList", options))));
  data.buffer.push("\n    ");
  return buffer;
  }

  data.buffer.push("<section class=\"l-wrapper\">\n        <div class=\"l-content\">\n            \n            <header class=\"page-header\">\n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "payment.active", {hash:{},inverse:self.program(3, program3, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </header>\n            \n            <form id=\"fund-monthly\">\n                \n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "payment.active", {hash:{},inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                \n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "payment.active", {hash:{},inverse:self.noop,fn:self.program(34, program34, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n            </form>\n        </div>\n\n        <div class=\"l-sidebar\">\n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "payment.active", {hash:{},inverse:self.noop,fn:self.program(36, program36, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n        </div>\n    </section>\n\n    ");
  hashContexts = {'id': depth0,'class': depth0};
  hashTypes = {'id': "STRING",'class': "STRING"};
  options = {hash:{
    'id': ("projectPicker"),
    'class': ("large compact")
  },inverse:self.noop,fn:self.program(38, program38, data),contexts:[],types:[],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers['bb-modal'] || depth0['bb-modal']),stack1 ? stack1.call(depth0, options) : helperMissing.call(depth0, "bb-modal", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  return buffer;
  
});Ember.TEMPLATES['userOrders'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, self=this, helperMissing=helpers.helperMissing;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n                <legend class=\"form-intro\">\n                    <strong>Edit your payment info</strong>\n                    <p>Here you can change your bank account info and monthly donations.</p>\n                </legend>\n\n                <fieldset>\n                    <ul>\n                        <li class=\"control-group\">\n                            <label class=\"control-label\">Account Name</label>\n                            <div class=\"controls\">\n                                ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("name"),
    'placeholder': ("Full name as it appears on your bank account"),
    'classBinding': ("errors.name.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                            </div>\n                            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.name", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                        </li>\n\n                        <li class=\"control-group\">\n                            <label class=\"control-label\">Account City</label>\n                            <div class=\"controls\">\n                                ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("city"),
    'placeholder': ("City registered on your bank account"),
    'classBinding': ("errors.city.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                            </div>\n                            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.city", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                        </li>\n\n                        <li class=\"control-group\">\n                            <label class=\"control-label\">Account Number</label>\n                            <div class=\"controls\">\n                                ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("account"),
    'placeholder': ("Your bank account number"),
    'classBinding': ("errors.account.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                            </div>\n                            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.account", {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                        </li>\n                    </ul>\n                </fieldset>\n\n                <fieldset>\n                    <ul>\n                        <li class=\"control-group\">\n                            <label class=\"control-label\">\n                                Monthly donations\n                            </label>\n\n                            <div class=\"controls\">\n                                ");
  hashContexts = {'name': depth0,'selectedValueBinding': depth0,'class': depth0};
  hashTypes = {'name': "STRING",'selectedValueBinding': "STRING",'class': "STRING"};
  stack1 = helpers.view.call(depth0, "Em.RadioButtonGroup", {hash:{
    'name': ("active"),
    'selectedValueBinding': ("recurringPaymentActive"),
    'class': ("radio-group-horizontal")
  },inverse:self.noop,fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                            </div>\n                        </li>\n                    </ul>\n                </fieldset>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "saved", {hash:{},inverse:self.noop,fn:self.program(11, program11, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n                <button class=\"btn btn-iconed btn-primary\">\n                    <em class=\"flaticon solid checkmark-1\"></em>\n                    ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "saveButtonText", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                </button>\n            ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                                <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.name", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                            ");
  return buffer;
  }
function program3(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program5(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                                <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.city", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                            ");
  return buffer;
  }

function program7(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                                <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.account", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                            ");
  return buffer;
  }

function program9(depth0,data) {
  
  var buffer = '', hashContexts, hashTypes;
  data.buffer.push("\n                                    <div class=\"radio3\">");
  hashContexts = {'value': depth0};
  hashTypes = {'value': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': ("on")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("<span>On</span></div>\n                                    <div class=\"radio3\">");
  hashContexts = {'value': depth0};
  hashTypes = {'value': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': ("off")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("<span>Off</span></div>\n                                    <a href=\"#\" class=\"ember-view edit-monthly-donations\">\n                                        <strong>View or edit monthly projects</strong>\n                                    </a>\n                                ");
  return buffer;
  }

function program11(depth0,data) {
  
  
  data.buffer.push("\n                    <span class=\"is-saved\"><em class=\"flaticon solid checkmark-1\"> Monthly settings saved</em></span>\n                ");
  }

function program13(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                    <ul>\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "order", "in", "closedOrders", {hash:{},inverse:self.noop,fn:self.program(14, program14, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </ul>\n                ");
  return buffer;
  }
function program14(depth0,data) {
  
  var buffer = '', stack1, stack2, hashContexts, hashTypes, options;
  data.buffer.push("\n                            <li>\n                                <small>");
  hashContexts = {'formatting': depth0};
  hashTypes = {'formatting': "STRING"};
  options = {hash:{
    'formatting': ("d")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "order.created", options) : helperMissing.call(depth0, "localize", "order.created", options))));
  data.buffer.push("</small>\n                                ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "order.recurring", {hash:{},inverse:self.program(17, program17, data),fn:self.program(15, program15, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push(" <strong> &euro;");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "order.total", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(",-</strong>\n                                <ul class=\"order-donations\">\n                                    ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers.each.call(depth0, "donation", "in", "order.donations", {hash:{},inverse:self.noop,fn:self.program(19, program19, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                                </ul>\n                            </li>\n                        ");
  return buffer;
  }
function program15(depth0,data) {
  
  
  data.buffer.push(" Monthly Donation ");
  }

function program17(depth0,data) {
  
  
  data.buffer.push(" Single Donation ");
  }

function program19(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                                        <li>\n                                            <a>\n                                                ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "donation.project.title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                                            </a>\n                                            <small> &euro;");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "donation.amount", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(",-</small>\n                                        </li>\n                                    ");
  return buffer;
  }

function program21(depth0,data) {
  
  
  data.buffer.push("\n                    <span class=\"is-loading-big\">Loading&#8230;</span>\n                ");
  }

  data.buffer.push("<section class=\"l-wrapper\">\n    <article class=\"l-content\">\n        <form>\n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "model", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n            <div class=\"order-history lined-list\">\n            <h2 class=\"form-summary\">Order History</h2>\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "closedOrders.isLoaded", {hash:{},inverse:self.program(21, program21, data),fn:self.program(13, program13, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n            </div>\n		</form>\n    </article>\n</section>");
  return buffer;
  
});Ember.TEMPLATES['userProfile'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n        <form>\n            <legend class=\"form-intro\">\n                <strong>Edit your profile</strong>\n                <p>Personalise your account so 1%Members can get to know you.</p>\n            </legend>\n\n            <fieldset>\n                <ul>\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">\n                            Name\n                        </label>\n\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'class': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'class': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("first_name"),
    'placeholder': ("First name"),
    'class': ("inline-prepend"),
    'classBinding': ("errors.first_name.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                            ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'class': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'class': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("last_name"),
    'placeholder': ("Surname"),
    'class': ("inline-append"),
    'classBinding': ("errors.last_name.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n\n                        \n                    </li>\n\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">\n                            Profile Picture\n                        </label>\n\n                        <div class=\"controls profile-pic-uploader\">\n                            <img>\n\n                            <a class=\"btn btn-iconed btn-uploader\">\n                                ");
  hashContexts = {'contentBinding': depth0,'name': depth0,'id': depth0,'accept': depth0};
  hashTypes = {'contentBinding': "STRING",'name': "STRING",'id': "STRING",'accept': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.UploadFileView", {hash:{
    'contentBinding': ("this"),
    'name': ("picture"),
    'id': ("picture"),
    'accept': ("image/*")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                                <em class=\"flaticon solid upload-document-1\"></em>\n                                Upload picture\n                            </a>\n                        </div>\n                    </li>\n                </ul>\n            </fieldset>\n\n            <fieldset>\n                <ul>\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">\n                            About yourself\n                        </label>\n\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'valueBinding': depth0,'maxlength': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'maxlength': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextArea", {hash:{
    'valueBinding': ("about"),
    'maxlength': ("265"),
    'placeholder': ("Tell us a bit about yourself so we can get to know you!"),
    'classBinding': ("errors.about.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.about", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </li>\n\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">\n                            Why did you join 1%Club?\n                        </label>\n\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'valueBinding': depth0,'maxlength': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'maxlength': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextArea", {hash:{
    'valueBinding': ("why"),
    'maxlength': ("265"),
    'placeholder': ("Tell the world why you chose to join 1%CLUB!"),
    'classBinding': ("errors.why.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.why", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </li>\n\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">\n                            Your website\n                        </label>\n\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("website"),
    'placeholder': ("http://"),
    'classBinding': ("errors.website.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.website", {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </li>\n\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">\n                            Location\n                        </label>\n\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("location"),
    'classBinding': ("errors.location.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.location", {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </li>\n                </ul>\n            </fieldset>\n            \n            <fieldset>\n                <legend>\n                	<strong>1%Skills</strong>\n                    <p>How much time are you willing to spend your 1%Skills?<br>Let us know so we can provide you with some matching tasks from our projects.</p>\n                </legend>\n\n                <ul>\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">\n                            Time available\n                        </label>\n\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'contentBinding': depth0,'optionValuePath': depth0,'optionLabelPath': depth0,'valueBinding': depth0};
  hashTypes = {'contentBinding': "STRING",'optionValuePath': "STRING",'optionLabelPath': "STRING",'valueBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.Select", {hash:{
    'contentBinding': ("timeAvailableList"),
    'optionValuePath': ("content.value"),
    'optionLabelPath': ("content.name"),
    'valueBinding': ("availability")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.availability", {hash:{},inverse:self.noop,fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </li>\n                </ul>\n            </fieldset>\n\n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "saved", {hash:{},inverse:self.noop,fn:self.program(11, program11, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n            <button class=\"btn btn-iconed btn-primary\">\n                <em class=\"flaticon solid checkmark-1\"></em>\n                ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "saveButtonText", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n            </button>\n        </form>\n    </article>\n</section>\n\n\n");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.about", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                        ");
  return buffer;
  }
function program3(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program5(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.why", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                        ");
  return buffer;
  }

function program7(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.website", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                        ");
  return buffer;
  }

function program9(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.availability", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                        ");
  return buffer;
  }

function program11(depth0,data) {
  
  
  data.buffer.push("\n                <span class=\"is-saved\"><em class=\"flaticon solid checkmark-1\"> Profile saved</em></span>\n            ");
  }

function program13(depth0,data) {
  
  
  data.buffer.push("\n    <span class=\"is-loading-big\">Loading&#8230;</span>\n");
  }

  data.buffer.push("<section class=\"l-wrapper\">\n    <article class=\"l-content\">\n        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isLoaded", {hash:{},inverse:self.program(13, program13, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  return buffer;
  
});Ember.TEMPLATES['userSettings'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n        <form>\n            <legend class=\"form-intro\">\n                <strong>Edit your account</strong>\n                <p>These are the details we currently have for you – update or change them below.</p>\n            </legend>\n\n            <fieldset>\n                <ul>\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">\n                            Email Address\n                        </label>\n\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("email"),
    'classBinding': ("errors.email.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.email", {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </li>\n                </ul>\n            </fieldset>\n            \n            <fieldset>\n                <ul>\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">\n                            I'd like to receive emails about\n                        </label>\n\n                        <div class=\"controls\">\n                            <label class=\"checkbox\">\n                                ");
  hashContexts = {'checkedBinding': depth0};
  hashTypes = {'checkedBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.Checkbox", {hash:{
    'checkedBinding': ("newsletter")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                                <span for=\"optionsCheckboxes1\">1%News</span>\n                            </label>\n                        </div>\n                    </li>\n                </ul>\n            </fieldset>\n\n            <fieldset>\n                <ul>\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">\n                            Account type\n                        </label>\n\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'contentBinding': depth0,'optionValuePath': depth0,'optionLabelPath': depth0,'valueBinding': depth0};
  hashTypes = {'contentBinding': "STRING",'optionValuePath': "STRING",'optionLabelPath': "STRING",'valueBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.Select", {hash:{
    'contentBinding': ("userTypeList"),
    'optionValuePath': ("content.value"),
    'optionLabelPath': ("content.name"),
    'valueBinding': ("user_type")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.user_type", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </li>\n\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">\n                            Primary language\n                        </label>\n\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'contentBinding': depth0,'optionValuePath': depth0,'optionLabelPath': depth0,'valueBinding': depth0};
  hashTypes = {'contentBinding': "STRING",'optionValuePath': "STRING",'optionLabelPath': "STRING",'valueBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.Select", {hash:{
    'contentBinding': ("App.interfaceLanguages"),
    'optionValuePath': ("content.code"),
    'optionLabelPath': ("content.name"),
    'valueBinding': ("primary_language")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.user_type", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </li>\n\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">\n                            I want to share\n                        </label>\n\n                        <div class=\"controls\">\n                            <label class=\"checkbox\">\n                                ");
  hashContexts = {'checkedBinding': depth0};
  hashTypes = {'checkedBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.Checkbox", {hash:{
    'checkedBinding': ("share_time_knowledge")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                                <span for=\"optionsCheckboxes1\">Time & Knowledge</span>\n                            </label>\n                            <label class=\"checkbox\">\n                                ");
  hashContexts = {'checkedBinding': depth0};
  hashTypes = {'checkedBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.Checkbox", {hash:{
    'checkedBinding': ("share_money")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                                <span for=\"optionsCheckboxes1\">Money</span>\n                            </label>\n                        </div>\n                    </li>\n                </ul>\n            </fieldset>\n\n            <fieldset>\n                <legend>\n                    <strong>Personal Details</strong>\n                    <p>We'd like to match you to projects and events based on your location & a personal thank you in your mailbox.</p>\n                </legend>\n                <ul>\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">\n                            Address Line 1\n                        </label>\n\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("line1"),
    'classBinding': ("errors.line1.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.line1", {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </li>\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">\n                            Address Line 2\n                        </label>\n\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("line2"),
    'classBinding': ("errors.line2.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.line2", {hash:{},inverse:self.noop,fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </li>\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">\n                            City\n                        </label>\n\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("city"),
    'classBinding': ("errors.city.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.city", {hash:{},inverse:self.noop,fn:self.program(11, program11, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </li>\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">\n                            Province / State\n                        </label>\n\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("state"),
    'classBinding': ("errors.state.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.state", {hash:{},inverse:self.noop,fn:self.program(13, program13, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </li>\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">\n                            Postal Code\n                        </label>\n\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("postal_code"),
    'classBinding': ("errors.postal_code.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.postal_code", {hash:{},inverse:self.noop,fn:self.program(15, program15, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n                    </li>\n\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">\n                            Country\n                        </label>\n\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.CountryCodeSelectView", {hash:{
    'valueBinding': ("country"),
    'placeholder': ("Country"),
    'classBinding': ("errors.country.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "error.country", {hash:{},inverse:self.noop,fn:self.program(17, program17, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </li>\n\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">\n                            Gender\n                        </label>\n\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'name': depth0,'selectedValueBinding': depth0,'class': depth0};
  hashTypes = {'name': "STRING",'selectedValueBinding': "STRING",'class': "STRING"};
  stack1 = helpers.view.call(depth0, "Em.RadioButtonGroup", {hash:{
    'name': ("gender"),
    'selectedValueBinding': ("gender"),
    'class': ("radio-group-horizontal")
  },inverse:self.noop,fn:self.program(19, program19, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                        </div>\n                    </li>\n\n                    <li class=\"control-group\">\n                        <label class=\"control-label\">\n                            Date of birth\n                        </label>\n\n                        <div class=\"controls\">\n                            ");
  hashContexts = {'valueBinding': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.DatePicker", {hash:{
    'valueBinding': ("birthdate"),
    'classBinding': ("errors.birthdate.length:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                        </div>\n\n                        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "errors.birthdate", {hash:{},inverse:self.noop,fn:self.program(21, program21, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                    </li>\n                </ul>\n            </fieldset>\n\n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "saved", {hash:{},inverse:self.noop,fn:self.program(23, program23, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n            <button class=\"btn btn-iconed btn-primary\">\n                <span class=\"flaticon solid checkmark-1\"><spanem>\n                ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "saveButtonText", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n            </button>\n        </form>\n    </article>\n</section>\n\n");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.email", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                        ");
  return buffer;
  }
function program3(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("<p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>");
  return buffer;
  }

function program5(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.user_type", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                        ");
  return buffer;
  }

function program7(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.line1", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                        ");
  return buffer;
  }

function program9(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.line2", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                        ");
  return buffer;
  }

function program11(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.city", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                        ");
  return buffer;
  }

function program13(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.state", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                        ");
  return buffer;
  }

function program15(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.postal_code", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                        ");
  return buffer;
  }

function program17(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.country", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                        ");
  return buffer;
  }

function program19(depth0,data) {
  
  var buffer = '', hashContexts, hashTypes;
  data.buffer.push("\n                                <label class=\"radio\" for=\"female\">");
  hashContexts = {'value': depth0,'id': depth0};
  hashTypes = {'value': "STRING",'id': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': ("female"),
    'id': ("female")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("<span>Female</span></label>\n                                <label class=\"radio\" for=\"male\">");
  hashContexts = {'value': depth0,'id': depth0};
  hashTypes = {'value': "STRING",'id': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': ("male"),
    'id': ("male")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("<span>Male</span></label>\n                                <label class=\"radio\" for=\"unset\">");
  hashContexts = {'value': depth0,'id': depth0};
  hashTypes = {'value': "STRING",'id': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "view.RadioButton", {hash:{
    'value': (""),
    'id': ("unset")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("<span>Unset</span></label>\n                            ");
  return buffer;
  }

function program21(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                            <div class=\"has-errors\">");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.birthdate", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("</div>\n                        ");
  return buffer;
  }

function program23(depth0,data) {
  
  
  data.buffer.push("\n                <span class=\"is-saved\"><em class=\"flaticon solid checkmark-1\"> Account settings saved</em></span>\n            ");
  }

function program25(depth0,data) {
  
  
  data.buffer.push("\n	<span class=\"is-loading-big\">Loading&#8230;</span>\n");
  }

  data.buffer.push("<section class=\"l-wrapper\">\n    <article class=\"l-content\">\n        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "isLoaded", {hash:{},inverse:self.program(25, program25, data),fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  return buffer;
  
});Ember.TEMPLATES['user_modal'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashContexts, hashTypes, escapeExpression=this.escapeExpression, self=this;

function program1(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n            <h3>About</h3>\n            <p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "about", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" </p>\n        ");
  return buffer;
  }

function program3(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n            <h4>Joined 1%Club because</h4>\n            <p>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "why", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" </p>\n        ");
  return buffer;
  }

function program5(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                <div class=\"um-list-item\">\n                    <em class=\"flaticon solid location-pin-1\"></em>\n                    <span class=\"key\">Location</span>\n                    <span class=\"value\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "location", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</span>\n                </div>\n            ");
  return buffer;
  }

function program7(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                <div class=\"um-list-item\">\n                    <em class=\"flaticon solid clock-1\"></em>\n                    <span class=\"key\">Time available</span>\n                    <span class=\"value\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "availability", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</span>\n                </div>\n            ");
  return buffer;
  }

function program9(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                <span class=\"um-meta-item website\">\n                    <a><em class=\"flaticon solid link-3\"></em>  ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "website", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</a>\n                </span>\n            ");
  return buffer;
  }

  data.buffer.push("<div class=\"user-modal-sidebar\">\n        <img ");
  hashContexts = {'src': depth0,'info': depth0};
  hashTypes = {'src': "STRING",'info': "STRING"};
  data.buffer.push(escapeExpression(helpers.bindAttr.call(depth0, {hash:{
    'src': ("getAvatar"),
    'info': ("first_name")
  },contexts:[],types:[],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" width=\"100\" height=\"100\"  />\n\n        <h2>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "first_name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "last_name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</h2>\n\n        <p class=\"um-member-since\">Member since ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "user_since", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</p>\n    </div>\n\n    <div class=\"user-modal-content\">\n        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "about", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "why", {hash:{},inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n        <div class=\"um-list\">\n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "location", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "availability", {hash:{},inverse:self.noop,fn:self.program(7, program7, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n        </div>\n\n        <div class=\"um-meta\">\n            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "website", {hash:{},inverse:self.noop,fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n        </div>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['voucher_donation'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, escapeExpression=this.escapeExpression, self=this, helperMissing=helpers.helperMissing;

function program1(depth0,data) {
  
  var buffer = '', hashContexts, hashTypes;
  data.buffer.push("\n        <img ");
  hashContexts = {'src': depth0,'alt': depth0};
  hashTypes = {'src': "STRING",'alt': "STRING"};
  data.buffer.push(escapeExpression(helpers.bindAttr.call(depth0, {hash:{
    'src': ("project.image_square"),
    'alt': ("project.title")
  },contexts:[],types:[],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" class=\"project-image\"  />\n        <h1>");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" <em class=\"country\"><i class=\"icon-globe\"></i> ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.country.name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</em></h1>\n    ");
  return buffer;
  }

  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "project", "project", options) : helperMissing.call(depth0, "linkTo", "project", "project", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n    <div class=\"donation-amount\">\n        <div class=\"amount-needed\">\n            \n            <strong>&euro; ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.campaign.money_needed", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong> is still needed\n        </div>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['voucher_pick_project'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, self=this, helperMissing=helpers.helperMissing;

function program1(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n            <li>\n                ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0,depth0],types:["STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "voucherRedeem.add", "project", options) : helperMissing.call(depth0, "linkTo", "voucherRedeem.add", "project", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n            </li>\n        ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                    ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "project.title", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                ");
  return buffer;
  }

  data.buffer.push("<h2>Pick a project</h2>\n    <ul>\n        ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "project", "in", "projects", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0,depth0,depth0],types:["ID","ID","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    </ul>");
  return buffer;
  
});Ember.TEMPLATES['voucher_redeem'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashContexts, hashTypes, options, self=this, helperMissing=helpers.helperMissing, escapeExpression=this.escapeExpression;

function program1(depth0,data) {
  
  
  data.buffer.push("\n                    <em class=\"icon-credit-card\"></em> Switch to donations\n                ");
  }

function program3(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n                    ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(4, program4, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "voucherRedeem", options) : helperMissing.call(depth0, "linkTo", "voucherRedeem", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                ");
  return buffer;
  }
function program4(depth0,data) {
  
  
  data.buffer.push("Support");
  }

function program6(depth0,data) {
  
  
  data.buffer.push("\n                    <a>Profile</a>\n                ");
  }

function program8(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n                <form class=\"labeled\">\n\n                    <fieldset>\n                        <ul>\n                            <li class=\"control-group control-group-lonely\">\n                                <label class=\"control-label\">Gift card ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "voucher.code", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" <i class=\"icon-ok\"></i></label>\n                            </li>\n                        </ul>\n                    </fieldset>\n\n                    <fieldset>\n                        <ul id=\"donation-projects\">\n                            ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "voucher.donations", {hash:{},inverse:self.program(11, program11, data),fn:self.program(9, program9, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                        </ul>\n                    </fieldset>\n\n                    <fieldset>\n                        <ul>\n                            <li class=\"form-summary\">\n                                Total\n                                <span class=\"currency right\">&euro;");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "voucher.amount", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</span>\n                            </li>\n                        </ul>\n                    </fieldset>\n\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "voucher.donations", {hash:{},inverse:self.noop,fn:self.program(13, program13, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n\n                    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "voucher.donations.length", {hash:{},inverse:self.program(17, program17, data),fn:self.program(15, program15, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                </form>\n\n            ");
  return buffer;
  }
function program9(depth0,data) {
  
  var buffer = '', hashContexts, hashTypes;
  data.buffer.push("\n                                ");
  hashContexts = {'content': depth0};
  hashTypes = {'content': "ID"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.VoucherDonationView", {hash:{
    'content': ("")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                            ");
  return buffer;
  }

function program11(depth0,data) {
  
  
  data.buffer.push("\n                                <a>\n                                    <div class=\"form-meta\">\n                                        <p class=\"form-label\">Choose a project to support with this gift card</p>\n                                        <p class=\"form-desc\">You can make it work!</p>\n                                    </div>\n                                </a>\n                            ");
  }

function program13(depth0,data) {
  
  
  data.buffer.push("\n                        <a>\n                            <em class=\"icon-retweet\"></em> Choose different project\n                        </a>\n                    ");
  }

function program15(depth0,data) {
  
  
  data.buffer.push("\n                        <button>\n                            <i class=\"icon icon-chevron-right\"></i>\n                            Submit\n                        </button>\n                    ");
  }

function program17(depth0,data) {
  
  
  data.buffer.push("\n                        <button disabled=\"disabled\" class=\"btn btn-iconed right\">\n                            <i class=\"icon icon-chevron-right\"></i>\n                            Submit\n                        </button>\n                    ");
  }

function program19(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n                <form class=\"labeled\">\n                    <fieldset>\n                        <ul>\n                            <li class=\"control-group\">\n                                <label class=\"control-label\">Gift card code</label>\n\n                                <div class=\"controls\">\n                                    ");
  hashContexts = {'valueBinding': depth0,'placeholder': depth0,'classBinding': depth0};
  hashTypes = {'valueBinding': "STRING",'placeholder': "STRING",'classBinding': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextField", {hash:{
    'valueBinding': ("code"),
    'placeholder': ("Your code"),
    'classBinding': ("error:error")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                                </div>\n\n                                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "error", {hash:{},inverse:self.noop,fn:self.program(20, program20, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                            </li>\n                        </ul>\n                    </fieldset>\n\n                    <button>\n                        <i class=\"icon icon-chevron-right\"></i>\n                        Submit\n                    </button>\n                </form>\n            ");
  return buffer;
  }
function program20(depth0,data) {
  
  
  data.buffer.push("\n                                    <div class=\"errors\"><p>Unfortunately we couldn't find a gift card with this code. Try entering the code again or send us a message and we will sort it out.</p></div>\n                                ");
  }

  data.buffer.push("<div class=\"container section\">\n        <div class=\"wrapper\">\n            <div class=\"content\">\n                <h1 class=\"main-title\">Redeem your 1%GIFTCARD and support a project!</h1>\n            </div>\n            <sidebar>\n                ");
  hashContexts = {'tagName': depth0,'class': depth0};
  hashTypes = {'tagName': "STRING",'class': "STRING"};
  options = {hash:{
    'tagName': ("a"),
    'class': ("button-link")
  },inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "currentOrder.donationList", options) : helperMissing.call(depth0, "linkTo", "currentOrder.donationList", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n            </sidebar>\n        </div>\n    </div>\n\n    <div class=\"container\">\n\n        <section class=\"wrapper\">\n\n            <ul class=\"voucher-steps\">\n                ");
  hashContexts = {'classNames': depth0};
  hashTypes = {'classNames': "STRING"};
  stack2 = helpers.view.call(depth0, "App.OrderNavView", {hash:{
    'classNames': ("support selected")
  },inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                ");
  hashContexts = {'classNames': depth0};
  hashTypes = {'classNames': "STRING"};
  stack2 = helpers.view.call(depth0, "App.OrderNavView", {hash:{
    'classNames': ("profile")
  },inverse:self.noop,fn:self.program(6, program6, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n            </ul>\n\n            ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "voucher.isLoaded", {hash:{},inverse:self.program(19, program19, data),fn:self.program(8, program8, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n\n        </section>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['voucher_redeem_done'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  


  data.buffer.push("<div class=\"container section\">\n\n        <header class=\"wrapper\">\n            <h1 class=\"\">YOU MAKE IT WORK!</h1>\n        </header>\n\n    </div>");
  
});Ember.TEMPLATES['voucher_start'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashContexts, hashTypes, options, self=this, helperMissing=helpers.helperMissing;

function program1(depth0,data) {
  
  
  data.buffer.push("\n                    <i class=\"icon icon-credit-card\"></i>\n\n                    <div class=\"btn-content\">\n                        <div class=\"btn-title\">I received a 1%GIFTCARD</div>\n                        <div class=\"btn-subtitle\">Support a project by cashing your voucher</div>\n                    </div>\n                ");
  }

function program3(depth0,data) {
  
  
  data.buffer.push("\n                    <i class=\"icon icon-gift\"></i>\n\n                    <div class=\"btn-content\">\n                        <div class=\"btn-title\">I'd like to buy a 1%GIFTCARD</div>\n                        <div class=\"btn-subtitle\">Order your digital email-vouchers right here!</div>\n                    </div>\n\n                ");
  }

function program5(depth0,data) {
  
  
  data.buffer.push("\n                        Contact us!\n                    ");
  }

  data.buffer.push("<div class=\"container section voucher-banner\">\n\n        <header class=\"wrapper\">\n            <div class=\"voucher-banner-title\">\n                <h1 class=\"\">Give</h1>\n                <h1 class=\"\">a gift</h1>\n                <h1 class=\"\">that keeps on giving</h1>\n                <h1 class=\"pink\">Give a</h1>\n                <h1 class=\"pink\">1%GIFTCARD </h1>\n            </div>\n\n            <div class=\"voucher-banner-calltoaction\">\n\n\n                ");
  hashContexts = {'class': depth0};
  hashTypes = {'class': "STRING"};
  options = {hash:{
    'class': ("btn btn-large btn-iconed")
  },inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "voucherRedeem", options) : helperMissing.call(depth0, "linkTo", "voucherRedeem", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n\n\n\n                ");
  hashContexts = {'class': depth0};
  hashTypes = {'class': "STRING"};
  options = {hash:{
    'class': ("btn btn-large btn-iconed btn-primary")
  },inverse:self.noop,fn:self.program(3, program3, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "currentOrder.voucherList", options) : helperMissing.call(depth0, "linkTo", "currentOrder.voucherList", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n\n                <p class=\"text-right voucher-custom\">\n                    <i class=\"icon icon-certificate\"></i> Need a (large) batch or custom cards?\n                    ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "customVoucherRequest", options) : helperMissing.call(depth0, "linkTo", "customVoucherRequest", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n                </p>\n            </div>\n        </header>\n\n    </div>\n\n    <div class=\"container\">\n        <section class=\"wrapper\">\n            <ul class=\"voucher-instructions\">\n                <li>\n                    <div class=\"voucher-ins-step\">1</div>\n                    <h2>Give</h2>\n\n                    <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam porta, nisi a fermentum vehicula, sapien dui facilisis arcu, in ullamcorper nisl purus id neque.</p>\n                </li>\n\n                <li>\n                    <div class=\"voucher-ins-step\">2</div>\n                    <h2>Choose</h2>\n\n                    <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam porta, nisi a fermentum vehicula, sapien dui facilisis arcu, in ullamcorper nisl purus id neque.</p>\n                </li>\n\n                <li>\n                    <div class=\"voucher-ins-step\">3</div>\n                    <h2>Follow</h2>\n\n                    <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam porta, nisi a fermentum vehicula, sapien dui facilisis arcu, in ullamcorper nisl purus id neque.</p>\n                </li>\n            </ul>\n        </section>\n    </div>");
  return buffer;
  
});Ember.TEMPLATES['wallpost_reaction'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options, escapeExpression=this.escapeExpression, helperMissing=helpers.helperMissing, self=this;

function program1(depth0,data) {
  
  
  data.buffer.push("\n                    <a>Delete</a>\n                ");
  }

  data.buffer.push("<li class=\"reaction\">\n	    <header class=\"reaction-header\">\n        \n            <div class=\"reaction-member\">\n\n                <a ");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers.action.call(depth0, "openInBigBox", "memberProfile", "author", {hash:{},contexts:[depth0,depth0,depth0],types:["ID","STRING","ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" class=\"member\">\n                    <span class=\"member-avatar\">\n                        <img ");
  hashContexts = {'src': depth0};
  hashTypes = {'src': "STRING"};
  data.buffer.push(escapeExpression(helpers.bindAttr.call(depth0, {hash:{
    'src': ("author.getAvatar")
  },contexts:[],types:[],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push(" alt=\"");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "author.full_name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\"  />\n                    </span>\n                    <strong class=\"member-name\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "author.full_name", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</strong>\n                </a>\n            \n            </div>\n\n            <div class=\"reaction-meta\">\n                <em class=\"timestamp\">");
  hashContexts = {'formatting': depth0};
  hashTypes = {'formatting': "STRING"};
  options = {hash:{
    'formatting': ("X")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  data.buffer.push(escapeExpression(((stack1 = helpers.localize || depth0.localize),stack1 ? stack1.call(depth0, "created", options) : helperMissing.call(depth0, "localize", "created", options))));
  data.buffer.push("</em>\n                ");
  hashTypes = {};
  hashContexts = {};
  stack2 = helpers['if'].call(depth0, "isAuthor", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("\n            </div>\n \n	    </header>\n            \n        <div class=\"reaction-content\">\n            <div class=\"text\">");
  hashContexts = {'unescaped': depth0};
  hashTypes = {'unescaped': "STRING"};
  stack2 = helpers._triageMustache.call(depth0, "text", {hash:{
    'unescaped': ("true")
  },contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push("</div>\n        </div>\n        \n       \n        \n	</li>");
  return buffer;
  
});Ember.TEMPLATES['wallpost_reaction_list'] = Ember.Handlebars.template(function anonymous(Handlebars,depth0,helpers,partials,data) {
this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Ember.Handlebars.helpers); data = data || {};
  var buffer = '', stack1, hashTypes, hashContexts, escapeExpression=this.escapeExpression, self=this, helperMissing=helpers.helperMissing;

function program1(depth0,data) {
  
  var buffer = '', stack1, hashContexts, hashTypes;
  data.buffer.push("\n        <ul class=\"reactions\">\n            ");
  hashContexts = {'itemController': depth0};
  hashTypes = {'itemController': "STRING"};
  stack1 = helpers.each.call(depth0, "controller", {hash:{
    'itemController': ("wallpostReaction")
  },inverse:self.noop,fn:self.program(2, program2, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n        </ul>\n    ");
  return buffer;
  }
function program2(depth0,data) {
  
  var buffer = '', hashContexts, hashTypes;
  data.buffer.push("\n                ");
  hashContexts = {'content': depth0};
  hashTypes = {'content': "ID"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "App.WallpostReactionView", {hash:{
    'content': ("")
  },contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n            ");
  return buffer;
  }

function program4(depth0,data) {
  
  var buffer = '', stack1, hashTypes, hashContexts;
  data.buffer.push("\n    <form class=\"reaction-form\">\n        <fieldset>\n            <ul>\n            <li>\n                <span class=\"member-avatar\">\n                    <img>\n                </span>\n\n                ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers.each.call(depth0, "errors.text", {hash:{},inverse:self.noop,fn:self.program(5, program5, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n                ");
  hashContexts = {'placeholder': depth0,'valueBinding': depth0,'name': depth0,'class': depth0};
  hashTypes = {'placeholder': "STRING",'valueBinding': "STRING",'name': "STRING",'class': "STRING"};
  data.buffer.push(escapeExpression(helpers.view.call(depth0, "Em.TextArea", {hash:{
    'placeholder': ("Comment"),
    'valueBinding': ("newReaction.text"),
    'name': ("reaction"),
    'class': ("newReaction")
  },contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("\n                \n                <button class=\"btn\" type=\"submit\" id=\"reaction-post\">Post</button>\n            </li>\n            </ul>\n        </fieldset>\n    </form>\n    ");
  return buffer;
  }
function program5(depth0,data) {
  
  var buffer = '', hashTypes, hashContexts;
  data.buffer.push("\n                    <span class=\"error\">");
  hashTypes = {};
  hashContexts = {};
  data.buffer.push(escapeExpression(helpers._triageMustache.call(depth0, "", {hash:{},contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data})));
  data.buffer.push("</span>\n                ");
  return buffer;
  }

function program7(depth0,data) {
  
  var buffer = '', stack1, stack2, hashTypes, hashContexts, options;
  data.buffer.push("\n        <div class=\"login-box\"><a>Login</a> or become a ");
  hashTypes = {};
  hashContexts = {};
  options = {hash:{},inverse:self.noop,fn:self.program(8, program8, data),contexts:[depth0],types:["STRING"],hashContexts:hashContexts,hashTypes:hashTypes,data:data};
  stack2 = ((stack1 = helpers.linkTo || depth0.linkTo),stack1 ? stack1.call(depth0, "signup", options) : helperMissing.call(depth0, "linkTo", "signup", options));
  if(stack2 || stack2 === 0) { data.buffer.push(stack2); }
  data.buffer.push(" to leave a reaction.</div>\n    ");
  return buffer;
  }
function program8(depth0,data) {
  
  
  data.buffer.push("member");
  }

  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "model.length", {hash:{},inverse:self.noop,fn:self.program(1, program1, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  data.buffer.push("\n    \n    ");
  hashTypes = {};
  hashContexts = {};
  stack1 = helpers['if'].call(depth0, "controllers.currentUser.isAuthenticated", {hash:{},inverse:self.program(7, program7, data),fn:self.program(4, program4, data),contexts:[depth0],types:["ID"],hashContexts:hashContexts,hashTypes:hashTypes,data:data});
  if(stack1 || stack1 === 0) { data.buffer.push(stack1); }
  return buffer;
  
});