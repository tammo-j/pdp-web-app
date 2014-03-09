/**
 * The site object.
 */
var SiteCode = function() {
	var self = this;
	
	/**
	 * State data.
	 */
	self.items = {};
	self.elements = null;
	self.product = null;
	self.productTotalElement = null;
	
	/**
	 * Initializes the site.
	 */
	self.initialize = function(event)
	{
		$('[data-role="header"]').toolbar();

		self.elements = {
			'cartButton': $('#cart-button'),
		};
		
		// Listen page transitions.
		$(':mobile-pagecontainer').on('pagecontainerbeforetransition', self.pageCreated);
		$(document).on('pagechange', self.pageChanged);
		
		// Listen amount changes.
		$('#amount-field').on('change', self.updatePrice).on('click', function(event) { $(this).select(); });
		$('#amount-slider-form').on('change', self.updatePriceSlider);
	};
	
	/**
	 * Prepares a new page.
	 */
	self.pageCreated = function(event, ui)
	{
		var page = ui.toPage.eq(0); 
		var id = page.attr('id');
		if (id == 'product' || id == 'product2')
		{
			$('#back-button').attr('href', '#search');
			
			// Prepare selected product.
			self.product = {
				'id': id,
				'name': page.find('.name').text(),
				'price': parseFloat(page.find('.price').text().replace(/,/g, '.')),
				'amount': 0,
				'total': 0
			};
			self.productTotalElement = page.find('.total');			
		}
		else if (id == 'cart')
		{
			// Set back button.
			$('#back-button').attr('href', '#search');
			if (ui.options.fromPage)
			{
				var from = ui.options.fromPage.eq(0).attr('id');
				if (from == 'product' || from == 'product2')
				{
					$('#back-button').attr('href', '#' + from);					
				}
			}
			
			// Create cart items.
			var list = page.find('ul#cart-list');
			var tpl = list.find('li[data-id="tpl__"]');
			var e = null;
			var i = 0;
			list.empty();
			list.append(tpl);
			for (var id in self.items)
			{
				var item = self.items[id];
				if (item.amount > 0)
				{
					e = tpl.clone().attr('data-id', id).removeClass('hidden ui-first-child ui-last-child');
					e.find('a').eq(0).attr('href', '#' + item.id);
					e.find('a.ui-icon-delete').click(self.deleteCart);
					e.find('.name').text(item.name);
					e.find('.price').html(self.eur(item.total));
					if (i == 0)
					{
						e.addClass('ui-first-child');
					}
					list.append(e);
					i++;
				}
			}
			if (e != null)
			{
				e.addClass('ui-last-child');
			}
			self.updateCartPrice();
		}
	};
	
	/**
	 * Finishes up with a new page.
	 */
	self.pageChanged = function(event, data)
	{
		var step = data.toPage.attr('data-step');
		if (step && step == 2)
		{
			self.showStep(2);
			self.activateBack();
			self.activateCart();
			
			// Update amount in form.
			var amount = 0;
			var id = data.toPage.attr('id');
			if (self.items[id] != undefined)
			{
				amount = self.items[id].amount;
			}
			if (id == 'product')
			{
				$('#amount-field').val(amount * 1000).change();
			}
			else if (id == 'product2')
			{
				$('#amount-slider').val(amount).slider('refresh');
				$('#amount-slider-form').find('.ui-slider-handle').text(amount);
			}
		}
		else if (step && step == 3)
		{
			self.showStep(3);
			self.activateBack();
			self.activateCart(false);
		}
		else
		{
			self.showStep(1);
			self.activateBack(false);
			self.activateCart();
		}
	};

	/**
	 * Shows current step.
	 */
	self.showStep = function(step)
	{
		$('#step-title .ui-icon').removeClass('active').eq(step - 1).addClass('active');	
	};

	/**
	 * Activates the back button.
	 */
	self.activateBack = function(flag)
	{
		if (flag !== undefined && !flag)
		{
			$('#back-button').addClass('ui-disabled');
		}
		else
		{
			$('#back-button').removeClass('ui-disabled');		
		}
	};

	/**
	 * Activates the cart button.
	 */
	self.activateCart = function(flag)
	{
		if (flag !== undefined && !flag)
		{
			$('#cart-button').addClass('ui-disabled');
		}
		else
		{
			$('#cart-button').removeClass('ui-disabled');		
		}
	};

	/**
	 * Updates the total item price.
	 */
	self.updatePrice = function(event)
	{
		var str = $(this).val();
		if (str != undefined && str != '')
		{
			self.product.amount = parseInt(str) / 1000;
		}
		else
		{
			self.product.amount = 0;
		}
		self.product.total = self.product.price * self.product.amount;
		self.productTotalElement.html(self.eur(self.product.total));
		self.updateCart(self.product);
	};
	self.updatePriceSlider = function(event)
	{
		self.product.amount = parseFloat($('#amount-slider').val());
		self.product.total = self.product.price * self.product.amount;
		self.productTotalElement.html(self.eur(self.product.total));
		self.updateCart(self.product);
	};
	
	/**
	 * Sets an item in the shopping cart.
	 */
	self.updateCart = function(item)
	{
		self.items[item.id] = item;
		self.updateCartState();
	};
	
	/**
	 * Deletes an item in the shopping cart.
	 */
	self.deleteCart = function(event)
	{
		event.preventDefault();
		var id = $(this).parent('li').attr('data-id');
		delete self.items[id];
		$('#cart-list li[data-id="' + id + '"]').remove();
		self.updateFirstAndLastChild('ul#cart-list li:visible');
		self.updateCartState();
		self.updateCartPrice();
	}
	
	/**
	 * Updates the cart state.
	 */
	self.updateCartState = function()
	{
		for (var id in self.items)
		{
			if (self.items[id].amount > 0)
			{
				self.elements.cartButton.addClass('ui-highlite');
				return;
			}
		}
		self.elements.cartButton.removeClass('ui-highlite');
	};
	
	/**
	 * Updates the cart price.
	 */
	self.updateCartPrice = function()
	{
		var total = 0;
		for (var id in self.items)
		{
			total += self.items[id].total;
		}
		$('#cart-toolbar .total').html(self.eur(total));
	}
	
	/**
	 * Updates the ui-first-child and ui-last-child classes.
	 */
	self.updateFirstAndLastChild = function(selector)
	{
		var els = $(selector);
		els.removeClass('ui-first-child ui-last-child').first().addClass('ui-first-child');
		els.last().addClass('ui-last-child');
	};
	
	/**
	 * Formats euro value for view.
	 */
	self.eur = function(value)
	{
		return value.toFixed(2).replace(/\./g, ',') + ' &euro;';
	};
};

// Create the site.
var site = new SiteCode();
$(document).ready(site.initialize);
