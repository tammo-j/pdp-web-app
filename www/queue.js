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

		// Populate orders.
		$.mobile.loading('hide');
		self.populate(self.elements.list, 'tpl__', data,
			self.updateOrdersPopulateCB);

		// Return open forms.
		for ( var i in open)
		{
			self.elements.list.find('li[data-id="' + open[i] + '"]')
					.removeClass('minimized').find('form:hidden').toggle();
		}
		self.scheduleUpdateOrders();

		// Try to fix first child class.
		self.elements.list.find('form').find('li[data-id!="tpl2__"]:first')
				.addClass('ui-first-child');
	};
	self.updateOrdersPopulateCB = function(el, order, i)
	{
		var time = parseInt(order.left);
		el.find('.number').text('#' + order.number);
		el.find('.items').text(order.count + ' items');
		el.find('.time').text(order.estimated + ' (' + time + ' mins)');
		if (time < 0)
		{
			el.find('.time').addClass('late');
		}
		else
		{
			el.find('.time').removeClass('late');
		}

		// Toggle order items visibility.
		el.find('a').on(
			'click',
			function(event)
			{
				event.preventDefault();
				$(this).parent('li').toggleClass('minimized').find('form')
						.toggle();
			});
		if (i > 0)
		{
			el.addClass('minimized').find('form').hide();
		}

		var sign = el.find('.sign').on('click', self.signOrder);

		// Populate items.
		var s = self.populate(el.find('ul'), 'tpl2__', order.items,
			self.updateOrderItemPopulateCB);
		if (s == 'true')
		{
			sign.removeClass('hidden');
		}
		return true;
	};
	self.updateOrderItemPopulateCB = function(el, item, i)
	{
		status = false;
		if (item.state != 'queued')
		{
			self.markItem(el, item.state == 'canceled', undefined);
			status = true;
		}
		var name = item.name;
		if (item.code)
		{
			name += ' (' + item.code + ')';
		}
		el.find('.name').text(name);
		el.find('.right').text(item.amount);
		if (item.price > 0)
		{
			var p = parseFloat(item.price);
			el.find('.right').append(
				' <small>- ' + p.toFixed(2) + ' &euro;</small>');
		}

		el.find('.check').on('click', self.itemChecked);
		el.find('.delete').on('click', self.itemDeleted);
		return status;
	};

	/**
	 * Marks item that has been acted on.
	 */
	self.markItem = function(el, deleteFlag, queueFlag)
	{
		if (queueFlag)
		{
			el.find('a').removeClass('processed');
			el.find('a,button').removeClass('ui-alt-icon selected');
			return;
		}
		el.find('a').addClass('processed');
		el.find('a,button').addClass('ui-alt-icon').removeClass('selected');
		if (deleteFlag)
		{
			el.find('.delete').addClass('selected');
		}
		else
		{
			el.find('.check').addClass('selected');
		}
	};

	/**
	 * Hides order from the view.
	 */
	self.removeOrder = function(id)
	{
		var li = $('#order-list > li[data-id="' + id + '"]');
		li.hide('slow', function()
		{
			li.remove()
			var lis = $('#order-list > li:visible');
			if (lis.size() > 0)
			{
				lis.first().find('form:hidden').toggle();
			}
			else
			{
				$('#order-list > li[data-id="empty__"]').removeClass('hidden')
						.show();
			}
		});
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
		self.itemAction($(this).parent('li'), false);
	}
	self.itemDeleted = function(event)
	{
		self.itemAction($(this).parent('li'), true);
	}
	self.itemAction = function(li, deleteFlag)
	{
		self.updating = true;
		$.post(checkUrl, {
			'csrfmiddlewaretoken' : li.parents('form').find(
				'input[name="csrfmiddlewaretoken"]').val(),
			'item' : li.attr('data-id'),
			'cancel' : deleteFlag
		}, function(data)
		{
			if (data.ok)
			{
				var li = $('#order-list form li[data-id="' + data.item + '"]');
				self.markItem(li, deleteFlag, data.queued);
				var orli = $('#order-list > li[data-id="' + data.order + '"]');
				if (data.complete)
				{
					orli.find('.sign').removeClass('hidden');
				}
				else
				{
					orli.find('.sign').addClass('hidden');
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
	 * Signs order processed.
	 */
	self.signOrder = function(event)
	{
		self.updating = true;
		$.post(signUrl, {
			'csrfmiddlewaretoken' : $(this).parent('li').find(
				'form input[name="csrfmiddlewaretoken"]').val(),
			'order' : $(this).parent('li').attr('data-id')
		}, function(data)
		{
			if (data.ok)
			{
				self.removeOrder(data.order);
				if (printUrl != '')
				{
					var $form = $('#print-form');
					$form.find('input[name="number"]').val(data.number);
					$form.find('input[name="time"]').val(data.time);
					$.post(printUrl, $form.serialize());
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
	self.populate = function(list, tpl, listItems, decorateCB)
	{
		list.find('li[data-id="empty__"]').addClass('hidden');
		list.find('li:not(.hidden)').remove();
		var tpl = list.find('li[data-id="' + tpl + '"]');
		var e = null;
		var i = 0;
		var status = true;
		for ( var i in listItems)
		{
			var item = listItems[i];
			e = tpl.clone().attr('data-id', item.pk).removeClass(
				'hidden ui-first-child ui-last-child');
			status = status && decorateCB(e, item, i);
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
		return status;
	};

};

// Create the site.
var site = new SiteCode();
$(document).ready(site.initialize);
