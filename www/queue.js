/**
 * The site object.
 */
var SiteCode = function()
{
	var self = this;

	/**
	 * State data.
	 */
	self.elements = null;
	self.updating = false;

	/**
	 * Initializes the site.
	 */
	self.initialize = function(event)
	{

		self.elements = {
			'list' : $('#order-list')
		};

		$('#queue [data-role="footer"] a').on('click', function(event)
		{
			event.preventDefault();
			window.location.href = $(this).attr('href');
		});

		self.updateOrders();
	};

	/**
	 * Updates the order list.
	 */
	self.updateOrders = function()
	{
		if (self.updating)
		{
			self.scheduleUpdateOrders();
			return;
		}
		$.mobile.loading('show');
		$.getJSON(queueUrl, self.updateOrdersCB);
	};
	self.updateOrdersCB = function(data)
	{
		// Collect open forms.
		var open = [];
		self.elements.list.find('form:visible').each(function()
		{
			open.push($(this).parent('li').attr('data-id'));
		});

		// Load orders.
		$.mobile.loading('hide');
		self.populate(self.elements.list, data, self.updateOrdersPopulateCB);

		// Return open forms.
		for ( var i in open)
		{
			self.elements.list.find('li[data-id="' + open[i] + '"]').find(
				'form:hidden').toggle();
		}
		self.scheduleUpdateOrders();
	};
	self.updateOrdersPopulateCB = function(el, order, i)
	{
		el.find('.number').text(order.number);
		el.find('.time').text(order.left + ' mins left');

		// Toggle order items visibility.
		el.find('a').on('click', function(event)
		{
			event.preventDefault();
			$(this).parent('li').find('form').toggle();
		});
		if (i > 0)
		{
			el.find('form').hide();
		}

		// Add new checkboxes dynamically.
		var wrap = el.find('fieldset');
		var cb = $('<input type="checkbox" id="cb0" /><label for="cb0"><span class="name">Product name</span><span class="amount">0.00 kg</span></label>');
		for ( var i in order.items)
		{
			var e = cb.clone();
			wrap.append(e);
			var id = 'cb' + order.pk + 'i' + order.items[i].pk;
			e.filter('label').attr('for', id);
			e.filter('input').attr('id', id).attr('data-id', order.items[i].pk);
			if (order.items[i].served)
			{
				e.filter('input').prop('checked', true).prop('disabled', true);
			}
			e.find('.name').text(order.items[i].name);
			e.find('.amount').text(order.items[i].amount + ' kg');
		}
		wrap.find('input').checkboxradio().on('change', self.itemChecked);
		wrap.controlgroup();
	};

	/**
	 * Schedules update orders within some time.
	 */
	self.scheduleUpdateOrders = function()
	{
		setTimeout(self.updateOrders, 10000);
	};

	/**
	 * Checks item off the order.
	 */
	self.itemChecked = function(event)
	{
		self.updating = true;
		var input = $(this);
		$.post(checkUrl, {
			'csrfmiddlewaretoken' : input.parents('form').find(
				'input[name="csrfmiddlewaretoken"]').val(),
			'item' : input.attr('data-id')
		}, function(data)
		{
			if (data.ok)
			{
				$('#order-list input[data-id="' + data.item + '"]')
						.checkboxradio('disable');
				if (data.complete)
				{
					var li = $('#order-list li[data-id="' + data.order + '"]');
					li.hide('slow', function()
					{
						li.remove()
						var lis = $('#order-list li:visible');
						if (lis.size() > 0)
						{
							lis.first().find('form:hidden').toggle();
						}
						else
						{
							$('#order-list li[data-id="empty__"]').removeClass(
								'hidden').show();
						}
					});
				}
			}
			else
			{
				$.mobile.showPageLoadingMsg($.mobile.pageLoadErrorMessageTheme,
					$.mobile.pageLoadErrorMessage, true);
				setTimeout($.mobile.hidePageLoadingMsg, 1500);
			}
			self.updating = false;
		}, 'json');
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
		for ( var i in listItems)
		{
			var item = listItems[i];
			e = tpl.clone().attr('data-id', item.pk).removeClass(
				'hidden ui-first-child ui-last-child');
			decorateCB(e, item, i);
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

};

// Create the site.
var site = new SiteCode();
$(document).ready(site.initialize);
