/**
 * The site object.
 */
var SiteCode = function()
{
	var self = this;

	/**
	 * State data.
	 */
	self.page = 0;
	self.categoryId = null;
	self.search = null;
	self.product = null;
	self.items = {};
	self.elements = null;

	/**
	 * Initializes the site.
	 */
	self.initialize = function(event)
	{
		// Create toolbar.
		$('[data-role="header"]').toolbar();

		// Pick elements.
		self.elements = {
			'categoryList' : $('#category-list'),
			'productList' : $('#product-list'),
			'cartList' : $('#cart-list'),
			'backButton' : $('#back-button'),
			'cartButton' : $('#cart-button'),
			'searchField' : $('#search-field'),
			'productTotal' : $('#product-total'),
			'amountSlider' : null
		};

		// Listen page transitions.
		$(':mobile-pagecontainer').on('pagecontainerbeforetransition',
			self.beforePage);
		$(document).on('pagechange', self.pageChanged);

		// Listen widgets.
		self.elements.backButton.on('click', self.goBack);
		self.elements.searchField.on('keyup', self.searchProducts).on('change',
			self.searchProducts);
		$('#amount-slider-form').on(
			'slidecreate',
			function(event)
			{
				self.elements.amountSlider = $('#amount-slider').on('change',
					self.selectAmount);
				self.updateSlider();
			});
		$('#order-button').on('click', self.orderTicket);

		// Setup start page.
		self.setupPage($('#search'));
	};

	/**
	 * Prepares a page to be transitioned.
	 */
	self.beforePage = function(event, ui)
	{
		self.setupPage(ui.toPage.eq(0));
	};

	/**
	 * Creates page contents.
	 */
	self.setupPage = function(page)
	{
		var id = page.attr('id');

		// Search page.
		if (id == 'search')
		{
			self.elements.backButton.attr('href', '#null');
			self.elements.cartButton.removeClass('ui-disabled');
			self.page = 1;

			// Update categories on return.
			if (self.categoryId === null && self.search === null)
			{
				self.elements.backButton.addClass('ui-disabled');
				self.showCategories();
			}
			else
			{
				self.elements.backButton.removeClass('ui-disabled');
			}
		}

		// Product page.
		else if (id == 'product')
		{
			self.elements.backButton.attr('href', '#search');
			self.elements.backButton.removeClass('ui-disabled');
			self.elements.cartButton.removeClass('ui-disabled');
			self.page = 2;

			// Update product data.
			page.find('img.image').attr('src', self.product.image);
			page.find('.name').text(self.product.name);
			page.find('.price').html(self.eur(self.product.price_per_kg, true));

			// Update product selection.
			self.elements.productTotal.html('');
			if (self.elements.amountSlider !== null)
			{
				self.updateSlider();
			}

			// Update product details.
			var details = self.productDetails(self.product);
			var table = page.find('table.product-attributes');
			self.populateTable(table, details['attributes'], function(el, item)
			{
				el.find('th').text(item.label);
				el.find('td').text(item.value);
			});
			table = page.find('table.product-facts');
			self.populateTable(table, details['facts'], function(el, item)
			{
				el.find('.nam').text(item.label);
				el.find('.val').text(item.value);
				el.find('.per').text(item.percent);
			});
			if (details['facts'].length > 0)
			{
				table.show();
			}
			else
			{
				table.hide();
			}
		}

		// Shopping cart page.
		else if (id == 'cart')
		{
			// Configure return to previous page.
			if (self.page == 2)
			{
				self.elements.backButton.attr('href', '#product');
			}
			else
			{
				self.elements.backButton.attr('href', '#search');
			}
			self.elements.backButton.removeClass('ui-disabled');
			self.elements.cartButton.addClass('ui-disabled');
			self.page = 3;

			// Clean empty items.
			for ( var pk in self.items)
			{
				if (self.items[pk].amount <= 0)
				{
					delete self.items[pk];
				}
			}

			// Create cart items.
			var i = 0;
			self.populate(self.elements.cartList, self.items,
				function(el, item)
				{
					el.find('.name').text(item.object.name);
					el.find('.price').html(
						self.eur(item.amount * item.object.price_per_kg));
					el.find('a').eq(0).data('product', item.object).on('click',
						function(event)
						{
							self.product = $(this).data('product');
						});
					el.find('a.ui-icon-delete').on('click', self.deleteCart);
					i++;
				});
			if (i > 0)
			{
				$('#cart-toolbar a').removeClass('ui-disabled');
			}
			else
			{
				$('#cart-toolbar a').addClass('ui-disabled');
			}
			self.updateCartPrice();
		}

		// Checkout page.
		else if (id == 'ticket')
		{
			self.page = 4;
			$('#queue-number').text('1');
			$('#queue-time').text('5 min');
		}
	};

	/**
	 * Finishes up with a new page.
	 */
	self.pageChanged = function(event, data)
	{
		if (self.page < 4)
		{
			$('#step-title .ui-icon').removeClass('active').eq(self.page - 1)
					.addClass('active');
		}
	};

	/**
	 * Back button clicked.
	 */
	self.goBack = function(event)
	{
		if (self.page < 2)
		{
			if (self.page > 0 && self.categoryId !== null)
			{
				self.elements.backButton.addClass('ui-disabled');
				self.elements.searchField.val('');
				self.showCategories();
			}
		}
	};

	/**
	 * Shows product categories.
	 */
	self.showCategories = function()
	{
		self.categoryId = null;
		self.search = null;
		self.elements.categoryList.show();
		self.elements.productList.hide();
		$.mobile.loading('show');
		$.getJSON(categoriesUrl, function(data)
		{
			$.mobile.loading('hide');
			self.populate(self.elements.categoryList, data, function(el, item)
			{
				el.find('.name').text(item.name);
				el.find('img').attr('src', item.image);
				el.find('a').on('click', function(event)
				{
					event.preventDefault();
					self.showProducts($(this).parent('li').attr('data-id'));
				});
			});
		});
	};

	/**
	 * Shows product list.
	 */
	self.showProducts = function(categoryId, search)
	{
		self.elements.backButton.removeClass('ui-disabled');
		self.elements.categoryList.hide();
		self.elements.productList.show();
		$.mobile.loading('show');
		var url = null;
		if (search !== undefined)
		{
			url = searchUrl + '?q=' + encodeURIComponent(search);
		}
		else if (categoryId !== null)
		{
			self.categoryId = categoryId;
			url = categoryUrl + categoryId;
		}
		if (url != null)
		{
			$.getJSON(url, function(data)
			{
				$.mobile.loading('hide');
				self.populate(self.elements.productList, data, function(el,
						item)
				{
					el.find('.name').text(item.name);
					el.find('.price').html(self.eur(item.price_per_kg, true));
					el.find('img').attr('src', item.image);
					el.find('a').data('product', item).on('click',
						function(event)
						{
							self.product = $(this).data('product');
						});
				});
			});
		}
	};

	/**
	 * Searches and shows products.
	 */
	self.searchProducts = function(event)
	{
		var q = self.elements.searchField.val().trim();
		if (q.length > 0)
		{
			self.search = q;
			self.showProducts(null, q);
		}
		else if (self.categoryId !== null)
		{
			self.search = null;
			self.showProducts(self.categoryId);
		}
		else
		{
			self.search = null;
			self.showCategories();
		}
	};

	/**
	 * Updates slider parameters for the state.
	 */
	self.updateSlider = function()
	{
		if (self.product !== null)
		{
			var amount = 0;
			if (self.items[self.product.pk] !== undefined)
			{
				amount = self.items[self.product.pk].amount;
			}
			self.elements.amountSlider.attr('max', self.product.max_kg).attr(
				'step', self.product.step_kg).val(amount).slider('refresh');
			self.elements.amountSlider.parent('.ui-slider').find(
				'.ui-slider-handle').text(amount);
			self.elements.productTotal.html(self.eur(amount
				* self.product.price_per_kg));
		}
	}

	/**
	 * Selects a new amount using slider.
	 */
	self.selectAmount = function(event)
	{
		var amount = parseFloat(self.elements.amountSlider.val());
		self.elements.productTotal.html(self.eur(amount
			* self.product.price_per_kg));
		if (self.items[self.product.pk] !== undefined)
		{
			self.items[self.product.pk].amount = amount;
		}
		else
		{
			self.items[self.product.pk] = {
				'object' : self.product,
				'amount' : amount
			};
		}
		self.updateCartState();
	};

	/**
	 * Deletes an item in the shopping cart.
	 */
	self.deleteCart = function(event)
	{
		event.preventDefault();
		var pk = $(this).parent('li').remove().attr('data-id');
		delete self.items[pk];
		self.updateFirstAndLastChild(self.elements.cartList.find('li:visible'));
		self.updateCartState();
		self.updateCartPrice();
	};

	/**
	 * Updates the cart state.
	 */
	self.updateCartState = function()
	{
		for ( var pk in self.items)
		{
			if (self.items[pk].amount > 0)
			{
				self.elements.cartButton.addClass('ui-highlite');
				return;
			}
		}
		$('#cart-toolbar a').addClass('ui-disabled');
		self.elements.cartButton.removeClass('ui-highlite');
	};

	/**
	 * Updates the cart price.
	 */
	self.updateCartPrice = function()
	{
		var total = 0;
		for ( var pk in self.items)
		{
			total += self.items[pk].amount * self.items[pk].object.price_per_kg;
		}
		$('#cart-toolbar .total').html(self.eur(total));
	};

	/**
	 * Populates a list.
	 */
	self.populate = function(list, listItems, decorateCB)
	{
		list.find('li[data-id="empty__"]').addClass('hidden');
		list.find('li:not(.hidden)').remove();
		var tpl = list.find('li[data-id="tpl__"]');
		var e = null;
		var i = 0;
		for ( var id in listItems)
		{
			var item = listItems[id];
			e = tpl.clone().attr('data-id', id).removeClass(
				'hidden ui-first-child ui-last-child');
			decorateCB(e, item);
			if (i == 0)
			{
				e.addClass('ui-first-child');
			}
			list.append(e);
			i++;
		}
		if (e != null)
		{
			e.addClass('ui-last-child');
		}
		if (i == 0)
		{
			list.find('li[data-id="empty__"]').removeClass('hidden');
		}
	};

	/**
	 * Populates a table.
	 */
	self.populateTable = function(table, rowItems, decorateCB)
	{
		table.find('tr.details').remove();
		var tpl = table.find('tr[data-id="tpl__"]');
		var e = null;
		for ( var i in rowItems)
		{
			e = tpl.clone().removeAttr('data-id').removeClass('hidden')
					.addClass('details');
			decorateCB(e, rowItems[i]);
			table.append(e);
		}
	}

	/**
	 * Updates the ui-first-child and ui-last-child classes.
	 */
	self.updateFirstAndLastChild = function(selector)
	{
		var els = $(selector);
		els.removeClass('ui-first-child ui-last-child').first().addClass(
			'ui-first-child');
		els.last().addClass('ui-last-child');
	};

	/**
	 * Parses product details string to fields.
	 */
	self.productDetails = function(product)
	{
		var a = [];
		var f = [];
		if (product.code.trim().length > 0)
		{
			a.push({
				'label' : 'Code',
				'value' : product.code
			});
		}
		var lines = product.details.split('\n');
		var to_a = true;
		for ( var i in lines)
		{
			var line = lines[i].trim();
			var cols = line.split('|');
			if (to_a)
			{
				if (cols.length >= 2)
				{
					a.push({
						'label' : cols[0],
						'value' : cols[1]
					});
				}
				else if (line.length > 0 && line[0] == '-')
				{
					to_a = false;
				}
			}
			else if (cols.length >= 3)
			{
				f.push({
					'label' : cols[0],
					'value' : cols[1],
					'percent' : cols[2]
				});
			}
		}
		return {
			'attributes' : a,
			'facts' : f
		};
	};

	/**
	 * Formats euro value for view.
	 */
	self.eur = function(value, perWeight)
	{
		if (typeof value == 'string')
		{
			value = parseFloat(value);
		}
		var str = value.toFixed(2).replace(/\./g, ',');
		if (perWeight !== undefined && perWeight)
		{
			return str + ' &euro;/kg';
		}
		return str + ' &euro;';
	};

	/**
	 * Orders a ticket.
	 */
	self.orderTicket = function(event)
	{
		event.preventDefault();
		$.mobile.loading('show');
		var post = {'csrfmiddlewaretoken':$('#cart-toolbar form input').val()};
		var i = 0;
		for ( var pk in self.items)
		{
			post['product' + i] = pk;
			post['amount' + i] = self.items[pk].amount;
			i++;
		}
		$.post(orderUrl, post, function(data)
		{
			if (data.ok)
			{
				window.location.href = ticketUrl + '#' + data.number + '+' + data.time;
			}
			else
			{
				$.mobile.showPageLoadingMsg($.mobile.pageLoadErrorMessageTheme,
					$.mobile.pageLoadErrorMessage, true);
				setTimeout($.mobile.hidePageLoadingMsg, 1500);
			}
		}, 'json');
	}
};

// Create the site.
var site = new SiteCode();
$(document).ready(site.initialize);
